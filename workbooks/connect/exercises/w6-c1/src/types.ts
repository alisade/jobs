// Types for conversational analytics (Contact Lens) output, per the documented schemas:
//  - post-contact output file, Version 1.1.0 (adminguide: contact-lens-example-output-files)
//  - real-time segment stream event, Version 1.0.0 (adminguide: sample-real-time-contact-analysis-segment-stream)
// Only the fields this exercise uses are typed strictly; everything else is optional.

export type Role = "AGENT" | "CUSTOMER";
export type SentimentLabel = "POSITIVE" | "NEGATIVE" | "NEUTRAL" | "MIXED";

export interface Turn {
  BeginOffsetMillis: number;
  EndOffsetMillis: number;
  Id: string;
  ParticipantId: Role | string;
  Content: string;
  Sentiment?: SentimentLabel;
  LoudnessScore?: number[];
  IssuesDetected?: { CharacterOffsets: { BeginOffsetChar: number; EndOffsetChar: number }; Text?: string }[];
  Redaction?: { RedactedTimestamps: { BeginOffsetMillis: number; EndOffsetMillis: number }[] };
}

export interface PeriodScore { BeginOffsetMillis: number; EndOffsetMillis: number; Score: number }

export interface AnalysisFile {
  Version: string;
  AccountId: string;
  Channel: "VOICE" | "CHAT" | "EMAIL";
  ContentMetadata: {
    Output: "Raw" | "Redacted";
    RedactionTypes?: string[];
    RedactionTypesMetadata?: { PII?: { RedactionEntitiesRequested?: string[]; RedactionMaskMode?: string } };
  };
  JobStatus: string;
  LanguageCode: string;
  Participants: { ParticipantId: string; ParticipantRole: Role }[];
  Categories?: { MatchedCategories: string[]; MatchedDetails: Record<string, unknown> };
  ConversationCharacteristics: {
    TotalConversationDurationMillis: number;
    Sentiment?: {
      OverallSentiment: Partial<Record<Role, number>>;
      SentimentByPeriod?: { QUARTER?: Partial<Record<Role, PeriodScore[]>> };
    };
    Interruptions?: { InterruptionsByInterrupter: Partial<Record<Role, unknown[]>>; TotalCount: number; TotalTimeMillis: number };
    NonTalkTime?: { TotalTimeMillis: number; Instances: unknown[] };
    TalkTime?: { TotalTimeMillis: number; DetailsByParticipant: Partial<Record<Role, { TotalTimeMillis: number }>> };
    ContactSummary?: { PostContactSummary?: { Content: string } };
  };
  Transcript: Turn[];
}

/** A parsed, validated analysis: the contact id comes from the S3 object name, not the file body. */
export interface ContactAnalysis {
  contactId: string;
  channel: "VOICE" | "CHAT" | "EMAIL";
  file: AnalysisFile;
}

export interface ContactRecord { agentId: string; agentName: string; queue: string; channel: string }

export interface PhraseRule { ruleId: string; phrases: string[]; priority?: number; participant?: Role }
export interface CompliancePolicy {
  policyVersion: string;
  greeting: PhraseRule & { withinMillis: number };
  closing: PhraseRule & { lastAgentTurns: number };
  requiredDisclosure: PhraseRule & { priority: number };
  escalationLanguage: PhraseRule & { priority: number; participant: Role };
  prohibitedAgentLanguage: PhraseRule & { priority: number; participant: Role };
  realtime: { sustainedNegativeTurns: number };
  qaAssignmentGroup: string;
}

/** One compliance finding that needs a QA task. */
export interface Finding {
  contactId: string;
  ruleId: string;
  priority: number; // 1 highest
  /** transcript turn ids that triggered the finding (empty for "missing" findings) */
  turnIds: string[];
  /** offset of the first evidence turn, or null for missing-phrase findings */
  atMillis: number | null;
}

export interface ComplianceResult {
  contactId: string;
  greetingOk: boolean;
  closingOk: boolean;
  disclosureOk: boolean;
  /** true when greeting and closing are both met */
  adherent: boolean;
  escalation: boolean;
  prohibited: boolean;
  findings: Finding[];
}

export interface AgentKpi {
  agentId: string;
  agentName: string;
  contacts: number;
  avgCustomerSentiment: number; // mean of OverallSentiment.CUSTOMER, 2 decimals
  avgCustomerSentimentDelta: number; // mean of (last QUARTER score - first QUARTER score) for CUSTOMER, 2 decimals
  agentTalkRatio: number | null; // sum agent talk / sum total talk over VOICE contacts with TalkTime, 2 decimals
  agentInterruptionsPerContact: number; // 2 decimals
  adherenceRate: number; // adherent / contacts, 2 decimals
  disclosureRate: number; // disclosureOk / contacts, 2 decimals
  escalations: number;
  prohibited: number;
}

/** Real-time segment stream event (Kinesis record payload). */
export interface SegmentEvent {
  Version: string;
  Channel: string;
  AccountId: string;
  InstanceId: string;
  ContactId: string;
  LanguageCode: string;
  EventType: "STARTED" | "SEGMENTS" | "COMPLETED" | "FAILED";
  Segments?: Array<{
    Utterance?: { Id: string; TranscriptId: string; ParticipantId: string; ParticipantRole: Role; PartialContent: string; BeginOffsetMillis: number; EndOffsetMillis: number };
    Transcript?: { Id: string; ParticipantId: string; ParticipantRole: Role; Content: string; BeginOffsetMillis: number; EndOffsetMillis: number; Sentiment?: SentimentLabel };
    Categories?: { MatchedCategories: string[]; MatchedDetails: Record<string, unknown> };
    PostContactSummary?: { Content: string; Status: string };
  }>;
}

export interface RealtimeAlert {
  contactId: string;
  type: "ESCALATION_LANGUAGE" | "SUSTAINED_NEGATIVE";
  atMillis: number;
  transcriptId: string;
}
