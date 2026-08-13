import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";

import {
  type DecodedDeployData,
  ExecutionResult,
  type GenLayerChain,
  type GenLayerClient,
  type TransactionHash,
  TransactionStatus,
} from "genlayer-js/types";

const STUDIO_CHAIN_ID = "61999";
const BRADBURY_CHAIN_ID = "4221";
const STUDIO_RPC_HOST = "studio.genlayer.com";
const BRADBURY_RPC_HOST = "rpc-bradbury.genlayer.com";
const AUDITED_SOURCE_SHA256 =
  "1B8672668E7AFB0F14205D98A53D2B64BF250A7323A9708ADC2A5F49E5B3A6B5";

type ReceiptCompat = {
  status?: string | number;
  statusName?: string;
  status_name?: string;
  txExecutionResult?: number;
  txExecutionResultName?: string;
  tx_execution_result?: number;
  tx_execution_result_name?: string;
  data?: { contract_address?: string };
  to_address?: string;
  txDataDecoded?: DecodedDeployData;
  consensus_data?: {
    leader_receipt?: Array<{
      mode?: string;
      execution_result?: string;
      genvm_result?: { raw_error?: unknown };
      result?: { status?: string };
    }>;
  };
};

function receiptIsFinalized(receipt: ReceiptCompat): boolean {
  return (
    receipt.statusName === TransactionStatus.FINALIZED ||
    receipt.status_name === TransactionStatus.FINALIZED ||
    receipt.status === TransactionStatus.FINALIZED ||
    Number(receipt.status) === 7
  );
}

function receiptExecutionSucceeded(receipt: ReceiptCompat): boolean {
  const resultName =
    receipt.txExecutionResultName ?? receipt.tx_execution_result_name;
  if (resultName !== undefined) {
    return resultName === ExecutionResult.FINISHED_WITH_RETURN;
  }

  const resultNumber =
    receipt.txExecutionResult ?? receipt.tx_execution_result;
  if (resultNumber !== undefined) {
    return Number(resultNumber) === 1;
  }

  const leader = receipt.consensus_data?.leader_receipt?.find(
    (candidate) => candidate.mode === "leader",
  );
  return (
    leader?.execution_result === "SUCCESS" &&
    leader.genvm_result?.raw_error == null &&
    leader.result?.status === "return"
  );
}

function requiredDeploymentStage(): "studionet" | "bradbury" {
  const stage = process.env.QUESTIONZERO_DEPLOY_STAGE?.trim().toLowerCase();
  if (stage !== "studionet" && stage !== "bradbury") {
    throw new Error(
      "QUESTIONZERO_DEPLOY_STAGE must be explicitly set to studionet or bradbury",
    );
  }
  return stage;
}

function positiveInteger(name: string, fallback: number): number {
  const raw = process.env[name]?.trim();
  if (!raw) return fallback;
  const value = Number(raw);
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error(`${name} must be a positive integer`);
  }
  return value;
}

export default async function main(client: GenLayerClient<GenLayerChain>) {
  const deploymentStage = requiredDeploymentStage();
  const expectedChainId =
    deploymentStage === "studionet" ? STUDIO_CHAIN_ID : BRADBURY_CHAIN_ID;
  const expectedRpcHost =
    deploymentStage === "studionet" ? STUDIO_RPC_HOST : BRADBURY_RPC_HOST;
  const actualChainId = String((client.chain as GenLayerChain).id);
  if (actualChainId !== expectedChainId) {
    throw new Error(
      `Refusing ${deploymentStage} deployment on chain ${actualChainId}; expected ${expectedChainId}`,
    );
  }
  const configuredRpc = (client.chain as GenLayerChain).rpcUrls.default.http[0];
  if (!configuredRpc) {
    throw new Error("Refusing deployment without a configured network RPC");
  }
  let actualRpcHost: string;
  try {
    actualRpcHost = new URL(configuredRpc).hostname.toLowerCase();
  } catch {
    throw new Error(`Refusing deployment with an invalid RPC URL`);
  }
  if (actualRpcHost !== expectedRpcHost) {
    throw new Error(
      `Refusing ${deploymentStage} deployment through RPC host ${actualRpcHost}; expected ${expectedRpcHost}`,
    );
  }

  const policyVersion = positiveInteger("QUESTIONZERO_POLICY_VERSION", 1);
  const receiptRetries = positiveInteger("QUESTIONZERO_RECEIPT_RETRIES", 1_440);
  const receiptIntervalMs = positiveInteger(
    "QUESTIONZERO_RECEIPT_INTERVAL_MS",
    5_000,
  );
  if (receiptRetries > 10_000) {
    throw new Error("QUESTIONZERO_RECEIPT_RETRIES cannot exceed 10000");
  }
  if (receiptIntervalMs < 1_000 || receiptIntervalMs > 60_000) {
    throw new Error(
      "QUESTIONZERO_RECEIPT_INTERVAL_MS must be between 1000 and 60000 ms",
    );
  }

  const contractPath = path.resolve(
    process.cwd(),
    "contracts/question_zero.py",
  );
  const code = new Uint8Array(readFileSync(contractPath));
  const sourceSha256 = createHash("sha256").update(code).digest("hex").toUpperCase();
  if (sourceSha256 !== AUDITED_SOURCE_SHA256) {
    throw new Error(
      `Refusing to deploy unaudited source ${sourceSha256}; expected ${AUDITED_SOURCE_SHA256}`,
    );
  }

  const hash = await client.deployContract({
    code,
    args: [policyVersion],
  });
  console.log(`Transaction: ${hash}`);

  const receipt = await client.waitForTransactionReceipt({
    hash: hash as TransactionHash,
    status: TransactionStatus.FINALIZED,
    retries: receiptRetries,
    interval: receiptIntervalMs,
  });
  const compatibleReceipt = receipt as unknown as ReceiptCompat;
  if (!receiptIsFinalized(compatibleReceipt)) {
    throw new Error(
      `Deployment did not finalize: status=${String(compatibleReceipt.statusName ?? compatibleReceipt.status_name ?? compatibleReceipt.status)}`,
    );
  }
  if (!receiptExecutionSucceeded(compatibleReceipt)) {
    throw new Error(
      `Deployment finalized but GenVM execution was not successful: result=${String(compatibleReceipt.txExecutionResultName ?? compatibleReceipt.tx_execution_result_name ?? compatibleReceipt.txExecutionResult ?? compatibleReceipt.tx_execution_result ?? "unknown")}`,
    );
  }

  const address =
    compatibleReceipt.data?.contract_address ??
    compatibleReceipt.txDataDecoded?.contractAddress ??
    compatibleReceipt.to_address;
  if (!address) {
    throw new Error(
      `Deployment finalized successfully without a contract address in the receipt`,
    );
  }

  console.log(`QuestionZero deployed at ${address}`);
  console.log(`Chain ID: ${actualChainId}`);
  console.log(`RPC host: ${actualRpcHost}`);
  console.log(`Policy version: ${policyVersion}`);
  console.log(`Source SHA-256: ${sourceSha256}`);
  return {
    address,
    hash,
    chainId: actualChainId,
    policyVersion,
    sourceSha256,
  };
}
