// Types for the routing simulator (given; do not change the shapes, the grader relies on them).

export type Proficiency = { attribute: string; value: string; level: number }; // level 1-5

/** One step of routing criteria: the agent must match ALL conditions. */
export type CriteriaStep = {
  /** seconds this step stays active; undefined = never expires */
  expirySeconds?: number;
  conditions: { attribute: string; value: string; minLevel: number }[];
};

export type RoutingProfileQueue = { queueId: string; priority: number; delaySeconds: number };
export type RoutingProfile = { id: string; queues: RoutingProfileQueue[] };
export type Agent = { id: string; routingProfileId: string; proficiencies?: Proficiency[] };
export type Queue = { id: string };

export type SimConfig = {
  queues: Queue[];
  routingProfiles: RoutingProfile[];
  agents: Agent[];
  serviceLevelThresholdSeconds: number;
};

export type Contact = {
  id: string;
  queueId: string;
  arrival: number; // integer seconds since start
  handleSeconds: number; // integer >= 1
  patienceSeconds: number; // abandons at arrival + patience if not answered before that second
  priority?: number; // contact priority in queue, 1 (highest) .. default 5
  timeAdjustmentSeconds?: number; // treated as if it arrived this many seconds earlier (ordering only)
  routingCriteria?: { steps: CriteriaStep[] };
};

export type ContactOutcome = {
  id: string;
  queueId: string;
  arrival: number;
  answeredAt: number | null;
  agentId: string | null;
  abandonedAt: number | null;
  waitSeconds: number; // until answer or abandon
};

export type QueueStats = {
  offered: number;
  handled: number;
  abandoned: number;
  answeredWithinThreshold: number;
  serviceLevel: number; // answeredWithinThreshold / offered (1 when offered = 0)
  asaSeconds: number; // mean wait of handled contacts (0 when none)
  maxWaitSeconds: number;
  abandonRate: number; // abandoned / offered
};

export type AgentStats = { handled: number; busySeconds: number; occupancy: number };

export type SimReport = {
  horizon: number; // second at which the last contact finished or abandoned
  queues: Record<string, QueueStats>;
  agents: Record<string, AgentStats>;
  overall: QueueStats;
  contacts: ContactOutcome[];
};
