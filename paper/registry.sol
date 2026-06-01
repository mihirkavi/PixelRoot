// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title PixelRootRegistry
/// @notice Batched, gas-amortized notarization of capture commitments.
///         Each shutter event produces a leaf h = SHA256(I || m); many leaves
///         are aggregated off-chain into a Merkle tree and only the root is
///         sealed on-chain, anchoring all member captures to one block time.
contract PixelRootRegistry {
    // root => block timestamp at which it was sealed (0 == unknown)
    mapping(bytes32 => uint64) public sealedAt;

    event RootRegistered(
        bytes32 indexed root,
        address indexed submitter,
        uint64  timestamp,
        uint256 leafCount
    );

    /// @notice Seal a Merkle root of capture commitments. Idempotent: a root
    ///         may be registered once; its block time is the proof-of-existence.
    function register(bytes32 root, uint256 leafCount) external {
        require(root != bytes32(0), "empty root");
        require(sealedAt[root] == 0, "already sealed");
        sealedAt[root] = uint64(block.timestamp);
        emit RootRegistered(root, msg.sender, uint64(block.timestamp), leafCount);
    }

    /// @notice True iff `leaf` is included under a sealed `root` via `proof`.
    ///         Pure verification path is free (eth_call); no state change.
    function verifyInclusion(
        bytes32 root,
        bytes32 leaf,
        bytes32[] calldata proof
    ) external view returns (bool included, uint64 timestamp) {
        if (sealedAt[root] == 0) return (false, 0);
        bytes32 node = leaf;
        for (uint256 i = 0; i < proof.length; i++) {
            bytes32 sib = proof[i];
            // sorted-pair hashing keeps proofs direction-agnostic
            node = node <= sib
                ? keccak256(abi.encodePacked(node, sib))
                : keccak256(abi.encodePacked(sib, node));
        }
        return (node == root, sealedAt[root]);
    }
}
