// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title PixelRootRegistry (v2)
/// @notice Public ledger for PixelRoot: manufacturer-certified sensor identities,
///         device revocation, and batched notarization of capture records.
///
///         Every Merkle tree in this contract (production lots of device keys and
///         batches of capture records) uses the same domain-separated SHA-256
///         construction, mirrored off-chain by experiments/ledger.py:
///             leaf = SHA-256(0x00 || item)
///             node = SHA-256(0x01 || min(a,b) || max(a,b))
///         An odd node at any level is promoted unchanged (never duplicated).
///
///         The contract records ledger facts only (who certified which sensor
///         keys, when a root was sealed, when a key was revoked). The capture
///         record's ECDSA signature by the sensor key is checked off-chain by the
///         verifier, which needs no secret.
contract PixelRootRegistry {
    struct Lot {
        address manufacturer; // certifying manufacturer
        uint64 sealedAt;      // block time the lot of sensor keys was certified
        uint32 deviceCount;   // informational
    }

    address public governance;

    /// manufacturer => block time it was admitted (0 == unknown)
    mapping(address => uint64) public manufacturerSince;
    /// manufacturer => block time it was revoked (0 == active)
    mapping(address => uint64) public manufacturerRevokedAt;
    /// lotKey(manufacturer, lot root) => lot. Keying by manufacturer means no
    /// party can claim, or revoke within, another manufacturer's lot.
    mapping(bytes32 => Lot) public lots;
    /// keccak256(lotKey, deviceKeyHash) => block time the sensor key was revoked
    mapping(bytes32 => uint64) public deviceRevokedAt;
    /// capture-batch root => when it was sealed (time 0 == unknown); one slot
    struct Seal {
        uint64 time;        // block timestamp
        uint64 blockNumber; // block number, compared with a record's anchor block
    }
    mapping(bytes32 => Seal) internal seals;

    event GovernanceTransferred(address indexed from, address indexed to);
    event ManufacturerAdded(address indexed manufacturer, uint64 timestamp);
    event ManufacturerRevoked(address indexed manufacturer, uint64 timestamp);
    event LotRegistered(bytes32 indexed lotRoot, address indexed manufacturer, uint64 timestamp, uint32 deviceCount);
    event DeviceRevoked(address indexed manufacturer, bytes32 indexed lotRoot, bytes32 indexed deviceKeyHash, uint64 timestamp);
    event RootRegistered(bytes32 indexed root, address indexed submitter, uint64 timestamp, uint64 blockNumber, uint256 leafCount);

    modifier onlyGovernance() {
        require(msg.sender == governance, "not governance");
        _;
    }

    constructor() {
        governance = msg.sender;
    }

    // ------------------------------------------------------------ governance

    function transferGovernance(address to) external onlyGovernance {
        require(to != address(0), "zero address");
        emit GovernanceTransferred(governance, to);
        governance = to;
    }

    function addManufacturer(address manufacturer) external onlyGovernance {
        require(manufacturer != address(0), "zero address");
        require(manufacturerSince[manufacturer] == 0, "already added");
        manufacturerSince[manufacturer] = uint64(block.timestamp);
        emit ManufacturerAdded(manufacturer, uint64(block.timestamp));
    }

    /// @notice Revoking a manufacturer invalidates every sensor it certified for
    ///         captures sealed at or after this block; earlier captures stand.
    function revokeManufacturer(address manufacturer) external onlyGovernance {
        require(manufacturerSince[manufacturer] != 0, "unknown manufacturer");
        require(manufacturerRevokedAt[manufacturer] == 0, "already revoked");
        manufacturerRevokedAt[manufacturer] = uint64(block.timestamp);
        emit ManufacturerRevoked(manufacturer, uint64(block.timestamp));
    }

    // ------------------------------------------------------- sensor identity

    /// @notice Certify a production lot: the Merkle root of the SHA-256 hashes of
    ///         the public keys generated inside each sensor at manufacture.
    function registerLot(bytes32 lotRoot, uint32 deviceCount) external {
        require(_isActiveManufacturer(msg.sender), "not an active manufacturer");
        require(lotRoot != bytes32(0), "empty root");
        bytes32 key = lotKey(msg.sender, lotRoot);
        require(lots[key].sealedAt == 0, "lot exists");
        lots[key] = Lot(msg.sender, uint64(block.timestamp), deviceCount);
        emit LotRegistered(lotRoot, msg.sender, uint64(block.timestamp), deviceCount);
    }

    /// @notice Revoke one sensor key (e.g. a compromised or stolen device). Only
    ///         the manufacturer that certified the lot may revoke its members.
    function revokeDevice(bytes32 lotRoot, bytes32 deviceKeyHash, bytes32[] calldata proof) external {
        bytes32 key = lotKey(msg.sender, lotRoot);
        require(lots[key].sealedAt != 0, "unknown lot");
        require(_verify(lotRoot, deviceKeyHash, proof), "device not in lot");
        bytes32 k = keccak256(abi.encodePacked(key, deviceKeyHash));
        require(deviceRevokedAt[k] == 0, "already revoked");
        deviceRevokedAt[k] = uint64(block.timestamp);
        emit DeviceRevoked(msg.sender, lotRoot, deviceKeyHash, uint64(block.timestamp));
    }

    // ---------------------------------------------------------- notarization
    // @listing-begin

    /// @notice Seal a Merkle root of capture-record hashes. Deliberately
    ///         permissionless (any device, app or batcher may submit, so no
    ///         party can censor a capture); `submitter` and `leafCount` are
    ///         informational and carry no trust. Authenticity comes from the
    ///         sensor signature inside each record, checked against the lots.
    function register(bytes32 root, uint256 leafCount) external {
        require(root != bytes32(0), "empty root");
        require(seals[root].time == 0, "already sealed");
        seals[root] = Seal(uint64(block.timestamp), uint64(block.number));
        emit RootRegistered(root, msg.sender, uint64(block.timestamp), uint64(block.number), leafCount);
    }

    // ----------------------------------------------------------- verification

    function sealedAt(bytes32 root) public view returns (uint64) {
        return seals[root].time;
    }

    function sealedBlock(bytes32 root) public view returns (uint64) {
        return seals[root].blockNumber;
    }

    function leafHash(bytes32 item) public pure returns (bytes32) {
        return sha256(abi.encodePacked(bytes1(0x00), item));
    }

    function lotKey(address manufacturer, bytes32 lotRoot) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(manufacturer, lotRoot));
    }

    /// @notice True iff `recordHash` is in a sealed capture batch `root`.
    function verifyInclusion(bytes32 root, bytes32 recordHash, bytes32[] calldata proof)
        external view returns (bool included, uint64 timestamp)
    {
        timestamp = seals[root].time;
        if (timestamp == 0) return (false, 0);
        return (_verify(root, recordHash, proof), timestamp);
    }

    /// @notice True iff `manufacturer` certified the sensor key in `lotRoot` no
    ///         later than time `t` and neither the key nor the manufacturer was
    ///         revoked by `t`.
    function deviceValidAt(
        address manufacturer,
        bytes32 lotRoot,
        bytes32 deviceKeyHash,
        bytes32[] calldata proof,
        uint64 t
    ) public view returns (bool) {
        bytes32 key = lotKey(manufacturer, lotRoot);
        Lot memory lot = lots[key];
        if (lot.sealedAt == 0 || lot.sealedAt > t) return false;
        uint64 mRev = manufacturerRevokedAt[manufacturer];
        if (mRev != 0 && mRev <= t) return false;
        uint64 dRev = deviceRevokedAt[keccak256(abi.encodePacked(key, deviceKeyHash))];
        if (dRev != 0 && dRev <= t) return false;
        return _verify(lotRoot, deviceKeyHash, proof);
    }

    /// @notice One-call ledger check for a capture: the record is sealed (at
    ///         `timestamp`, in block `blockNumber`, which the verifier compares
    ///         with the record's anchor block), and the signing sensor was valid
    ///         at the sealing time.
    function verifyCapture(
        bytes32 root,
        bytes32 recordHash,
        bytes32[] calldata proof,
        address manufacturer,
        bytes32 lotRoot,
        bytes32 deviceKeyHash,
        bytes32[] calldata deviceProof
    ) external view returns (bool included, uint64 timestamp, uint64 blockNumber, bool deviceValid) {
        Seal memory seal = seals[root];
        timestamp = seal.time;
        if (timestamp == 0) return (false, 0, 0, false);
        blockNumber = seal.blockNumber;
        included = _verify(root, recordHash, proof);
        deviceValid = deviceValidAt(manufacturer, lotRoot, deviceKeyHash, deviceProof, timestamp);
    }

    // @listing-end
    // -------------------------------------------------------------- internal

    function _isActiveManufacturer(address m) internal view returns (bool) {
        return manufacturerSince[m] != 0 && manufacturerRevokedAt[m] == 0;
    }

    function _verify(bytes32 root, bytes32 item, bytes32[] calldata proof) internal pure returns (bool) {
        bytes32 node = leafHash(item);
        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 sib = proof[i];
            node = node <= sib
                ? sha256(abi.encodePacked(bytes1(0x01), node, sib))
                : sha256(abi.encodePacked(bytes1(0x01), sib, node));
        }
        return node == root;
    }
}
