require("@nomicfoundation/hardhat-ethers");
require("@nomicfoundation/hardhat-chai-matchers");
const path = require("path");
const { subtask } = require("hardhat/config");
const { TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD } = require("hardhat/builtin-tasks/task-names");

const SOLC_VERSION = "0.8.24";

// Compile with the solc-js build pinned in package.json instead of downloading
// a compiler at build time, so tests run offline and reproducibly.
subtask(TASK_COMPILE_SOLIDITY_GET_SOLC_BUILD, async (args, hre, runSuper) => {
  if (args.solcVersion === SOLC_VERSION) {
    const compilerPath = path.join(__dirname, "node_modules", "solc", "soljson.js");
    return { compilerPath, isSolcJs: true, version: SOLC_VERSION, longVersion: SOLC_VERSION };
  }
  return runSuper();
});

module.exports = {
  solidity: { version: SOLC_VERSION, settings: { optimizer: { enabled: true, runs: 200 } } },
  paths: { sources: "./src", tests: "./test" },
};
