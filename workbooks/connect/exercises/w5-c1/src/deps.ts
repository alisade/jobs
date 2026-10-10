// Backends the code hook talks to. Production wires these to the identity directory and the
// password-reset service (both behind LFG's integration API); tests inject in-memory fakes.

export type DirectoryRecord = {
  employeeId: string; // five digits, e.g. "44129"
  displayName: string;
  department: string;
  status: "ACTIVE" | "LOCKED" | "DISABLED";
  mfaEnrolled: boolean;
  vip: boolean;
};

export interface Directory {
  /** Returns null when the employee id does not exist. */
  lookup(employeeId: string): Promise<DirectoryRecord | null>;
  unlock(employeeId: string): Promise<"UNLOCKED" | "NOT_LOCKED" | "FAILED">;
}

export interface ResetService {
  /** Sends a reset link to the employee's MFA device. "NO_MFA" when none is enrolled. */
  sendResetLink(employeeId: string, system: SystemCode): Promise<"SENT" | "NO_MFA" | "FAILED">;
}

/** Canonical values of the SystemName custom slot type (resolution: TopResolution). */
export type SystemCode = "EMAIL" | "VPN" | "SAP" | "SAP_CONCUR" | "WORKDAY";

export type Deps = { directory: Directory; reset: ResetService };
