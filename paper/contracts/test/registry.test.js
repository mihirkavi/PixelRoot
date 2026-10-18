const { expect } = require("chai");
const { ethers, network } = require("hardhat");
const crypto = require("crypto");
const vectors = require("./vectors.json");

// JS mirror of experiments/ledger.py (domain-separated, sorted-pair SHA-256).
const sha = (...bufs) => crypto.createHash("sha256").update(Buffer.concat(bufs)).digest();
const leaf = (x) => sha(Buffer.from([0]), x);
const node = (a, b) => (Buffer.compare(a, b) <= 0 ? sha(Buffer.from([1]), a, b) : sha(Buffer.from([1]), b, a));
function levels(items) {
  let lvl = items.map(leaf);
  const out = [lvl];
  while (lvl.length > 1) {
    const nxt = [];
    for (let i = 0; i < lvl.length; i += 2) nxt.push(i + 1 < lvl.length ? node(lvl[i], lvl[i + 1]) : lvl[i]);
    lvl = nxt;
    out.push(lvl);
  }
  return out;
}
const root = (items) => levels(items).at(-1)[0];
function proof(items, index) {
  const p = [];
  for (const lvl of levels(items).slice(0, -1)) {
    if ((index ^ 1) < lvl.length) p.push(lvl[index ^ 1]);
    index >>= 1;
  }
  return p;
}
const hex = (b) => "0x" + b.toString("hex");
const buf = (h) => Buffer.from(h.slice(2), "hex");
const rand = () => crypto.randomBytes(32);

async function advance(seconds) {
  await network.provider.send("evm_increaseTime", [seconds]);
  await network.provider.send("evm_mine");
}

describe("PixelRootRegistry", function () {
  let reg, gov, oem, oem2, anyone;
  const deviceKeys = Array.from({ length: 5 }, () => rand()); // SHA-256(sensor public key)
  let lotRoot;

  beforeEach(async function () {
    [gov, oem, oem2, anyone] = await ethers.getSigners();
    reg = await (await ethers.getContractFactory("PixelRootRegistry")).deploy();
    await reg.addManufacturer(oem.address);
    lotRoot = root(deviceKeys);
    await reg.connect(oem).registerLot(hex(lotRoot), deviceKeys.length);
  });

  describe("Merkle compatibility with experiments/ledger.py", function () {
    it("verifies every Python-generated vector (odd sizes, single leaf)", async function () {
      for (const [n, v] of Object.entries(vectors)) {
        await reg.connect(anyone).register(v.root, Number(n));
        for (let i = 0; i < v.items.length; i++) {
          const [ok] = await reg.verifyInclusion(v.root, v.items[i], v.proofs[i]);
          expect(ok, `n=${n} i=${i}`).to.equal(true);
          expect(hex(root(v.items.map(buf)))).to.equal(v.root);
        }
      }
    });

    it("leafHash matches SHA-256(0x00 || item)", async function () {
      const x = rand();
      expect(await reg.leafHash(hex(x))).to.equal(hex(leaf(x)));
    });

    it("rejects an internal node presented as a leaf (second-preimage guard)", async function () {
      const items = Array.from({ length: 4 }, () => rand());
      const r = root(items);
      await reg.register(hex(r), 4);
      const internal = levels(items)[1][0]; // parent of items 0 and 1
      const [ok] = await reg.verifyInclusion(hex(r), hex(internal), [hex(levels(items)[1][1])]);
      expect(ok).to.equal(false);
    });

    it("rejects a wrong proof and an unsealed root", async function () {
      const items = Array.from({ length: 3 }, () => rand());
      const r = root(items);
      let [ok, t] = await reg.verifyInclusion(hex(r), hex(items[0]), proof(items, 0).map(hex));
      expect(ok).to.equal(false);
      expect(t).to.equal(0n);
      await reg.register(hex(r), 3);
      [ok] = await reg.verifyInclusion(hex(r), hex(items[0]), proof(items, 1).map(hex));
      expect(ok).to.equal(false);
    });
  });

  describe("governance and manufacturers", function () {
    it("only governance admits or revokes manufacturers", async function () {
      await expect(reg.connect(anyone).addManufacturer(anyone.address)).to.be.revertedWith("not governance");
      await expect(reg.connect(anyone).revokeManufacturer(oem.address)).to.be.revertedWith("not governance");
      await expect(reg.addManufacturer(oem.address)).to.be.revertedWith("already added");
    });

    it("only active manufacturers certify lots; lots are write-once", async function () {
      await expect(reg.connect(anyone).registerLot(hex(rand()), 1)).to.be.revertedWith("not an active manufacturer");
      await expect(reg.connect(oem).registerLot(hex(lotRoot), 5)).to.be.revertedWith("lot exists");
      await reg.revokeManufacturer(oem.address);
      await expect(reg.connect(oem).registerLot(hex(rand()), 1)).to.be.revertedWith("not an active manufacturer");
    });

    it("transfers governance", async function () {
      await reg.transferGovernance(anyone.address);
      await expect(reg.addManufacturer(oem2.address)).to.be.revertedWith("not governance");
      await reg.connect(anyone).addManufacturer(oem2.address);
    });
  });

  describe("notarization", function () {
    it("is permissionless and write-once", async function () {
      const r = rand();
      await expect(reg.connect(anyone).register(hex(r), 10)).to.emit(reg, "RootRegistered");
      await expect(reg.connect(oem).register(hex(r), 10)).to.be.revertedWith("already sealed");
      await expect(reg.register(ethers.ZeroHash, 1)).to.be.revertedWith("empty root");
    });
  });

  describe("device validity and revocation", function () {
    async function capture(records) {
      const r = root(records);
      await reg.connect(anyone).register(hex(r), records.length);
      return r;
    }

    it("accepts a capture signed by a certified, unrevoked sensor", async function () {
      const recs = [rand(), rand(), rand()];
      const r = await capture(recs);
      const [inc, t, dev] = await reg.verifyCapture(
        hex(r), hex(recs[2]), proof(recs, 2).map(hex),
        hex(lotRoot), hex(deviceKeys[1]), proof(deviceKeys, 1).map(hex));
      expect(inc).to.equal(true);
      expect(t).to.be.greaterThan(0n);
      expect(dev).to.equal(true);
    });

    it("rejects a sensor key that is not in the lot", async function () {
      const recs = [rand()];
      const r = await capture(recs);
      const [, , dev] = await reg.verifyCapture(hex(r), hex(recs[0]), [],
        hex(lotRoot), hex(rand()), proof(deviceKeys, 0).map(hex));
      expect(dev).to.equal(false);
    });

    it("revocation is time-scoped: earlier captures stand, later ones fail", async function () {
      const before = [rand()];
      const rBefore = await capture(before);
      await advance(60);
      await reg.connect(oem).revokeDevice(hex(lotRoot), hex(deviceKeys[3]), proof(deviceKeys, 3).map(hex));
      await advance(60);
      const after = [rand()];
      const rAfter = await capture(after);
      const p = proof(deviceKeys, 3).map(hex);
      const [, , devBefore] = await reg.verifyCapture(hex(rBefore), hex(before[0]), [], hex(lotRoot), hex(deviceKeys[3]), p);
      const [, , devAfter] = await reg.verifyCapture(hex(rAfter), hex(after[0]), [], hex(lotRoot), hex(deviceKeys[3]), p);
      expect(devBefore).to.equal(true);
      expect(devAfter).to.equal(false);
      // other sensors in the lot are unaffected
      const [, , other] = await reg.verifyCapture(hex(rAfter), hex(after[0]), [], hex(lotRoot), hex(deviceKeys[0]), proof(deviceKeys, 0).map(hex));
      expect(other).to.equal(true);
    });

    it("only the certifying manufacturer can revoke, and only lot members", async function () {
      await reg.addManufacturer(oem2.address);
      const p = proof(deviceKeys, 0).map(hex);
      await expect(reg.connect(oem2).revokeDevice(hex(lotRoot), hex(deviceKeys[0]), p)).to.be.revertedWith("not lot manufacturer");
      await expect(reg.connect(oem).revokeDevice(hex(lotRoot), hex(rand()), p)).to.be.revertedWith("device not in lot");
      await reg.connect(oem).revokeDevice(hex(lotRoot), hex(deviceKeys[0]), p);
      await expect(reg.connect(oem).revokeDevice(hex(lotRoot), hex(deviceKeys[0]), p)).to.be.revertedWith("already revoked");
    });

    it("a malicious manufacturer cannot revoke another manufacturer's sensor", async function () {
      await reg.addManufacturer(oem2.address);
      const hostile = [deviceKeys[0], rand()]; // victim key copied into a hostile lot
      const hostileRoot = root(hostile);
      await reg.connect(oem2).registerLot(hex(hostileRoot), 2);
      await reg.connect(oem2).revokeDevice(hex(hostileRoot), hex(deviceKeys[0]), proof(hostile, 0).map(hex));
      await advance(30);
      const recs = [rand()];
      const r = await capture(recs);
      const [, , dev] = await reg.verifyCapture(hex(r), hex(recs[0]), [], hex(lotRoot), hex(deviceKeys[0]), proof(deviceKeys, 0).map(hex));
      expect(dev).to.equal(true);
    });

    it("manufacturer revocation invalidates its sensors from that time on", async function () {
      const before = [rand()];
      const rBefore = await capture(before);
      await advance(60);
      await reg.revokeManufacturer(oem.address);
      await advance(60);
      const after = [rand()];
      const rAfter = await capture(after);
      const p = proof(deviceKeys, 2).map(hex);
      expect((await reg.verifyCapture(hex(rBefore), hex(before[0]), [], hex(lotRoot), hex(deviceKeys[2]), p))[2]).to.equal(true);
      expect((await reg.verifyCapture(hex(rAfter), hex(after[0]), [], hex(lotRoot), hex(deviceKeys[2]), p))[2]).to.equal(false);
    });

    it("a lot certified after the capture does not validate it (no retroactive certification)", async function () {
      const recs = [rand()];
      const r = await capture(recs);
      await advance(60);
      const late = [rand(), rand()];
      await reg.connect(oem).registerLot(hex(root(late)), 2);
      const [, , dev] = await reg.verifyCapture(hex(r), hex(recs[0]), [], hex(root(late)), hex(late[0]), proof(late, 0).map(hex));
      expect(dev).to.equal(false);
    });
  });

  describe("gas (reported for the paper)", function () {
    it("measures transaction and verification costs", async function () {
      const g = async (tx) => (await (await tx).wait()).gasUsed;
      const sizes = [1, 100, 10000];
      const rows = [];
      for (const n of sizes) {
        rows.push([`register (batch of ${n})`, await g(reg.connect(anyone).register(hex(rand()), n))]);
      }
      rows.push(["registerLot", await g(reg.connect(oem).registerLot(hex(rand()), 100000))]);
      const big = Array.from({ length: 1024 }, () => rand());
      const bigRoot = root(big);
      await reg.connect(oem).registerLot(hex(bigRoot), 1024);
      rows.push(["revokeDevice (lot of 1024)", await g(reg.connect(oem).revokeDevice(hex(bigRoot), hex(big[7]), proof(big, 7).map(hex)))]);
      const recs = Array.from({ length: 10000 }, (_, i) => sha(Buffer.from(`rec${i}`)));
      const r = root(recs);
      await reg.register(hex(r), recs.length);
      const est = await reg.verifyCapture.estimateGas(hex(r), hex(recs[42]), proof(recs, 42).map(hex),
        hex(bigRoot), hex(big[3]), proof(big, 3).map(hex));
      rows.push(["verifyCapture (eth_call, 10^4 batch, 1024 lot)", est]);
      const byName = Object.fromEntries(rows);
      const report = {
        evm: `solc ${require("hardhat").config.solidity.compilers[0].version}, optimizer 200 runs, Hardhat network`,
        register: Number(byName["register (batch of 1)"]),
        registerLot: Number(byName["registerLot"]),
        revokeDevice: Number(byName["revokeDevice (lot of 1024)"]),
        verifyCapture: Number(byName["verifyCapture (eth_call, 10^4 batch, 1024 lot)"]),
      };
      require("fs").writeFileSync(require("path").join(__dirname, "..", "..", "experiments", "results", "gas_report.json"),
        JSON.stringify(report, null, 1) + "\n");
      console.log("\n      gas report");
      for (const [name, gas] of rows) console.log(`        ${name.padEnd(48)} ${gas}`);
      for (const n of sizes) console.log(`        amortized register per image @${n}`.padEnd(56) + (Number(rows[sizes.indexOf(n)][1]) / n).toFixed(2));
    });
  });
});
