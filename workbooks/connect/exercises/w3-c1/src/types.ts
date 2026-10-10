// Amazon Chime SDK PSTN audio: the event a SIP media application sends to its Lambda and the
// response it expects. Field names follow the Chime SDK developer guide ("Using the PSTN audio
// service" > invocation events / actions). Only the subset this application uses is typed.

export type InvocationEventType =
  | "NEW_INBOUND_CALL"
  | "NEW_OUTBOUND_CALL"
  | "ACTION_SUCCESSFUL"
  | "ACTION_FAILED"
  | "ACTION_INTERRUPTED"
  | "HANGUP"
  | "CALL_ANSWERED"
  | "INVALID_LAMBDA_RESPONSE"
  | "DIGITS_RECEIVED"
  | "CALL_UPDATE_REQUESTED";

export type ParticipantTag = "LEG-A" | "LEG-B";

export interface Participant {
  CallId: string;
  ParticipantTag: ParticipantTag;
  To: string;
  From: string;
  Direction: "Inbound" | "Outbound";
  StartTimeInMilliseconds: string;
  Status: "Connected" | "Disconnected";
  SipHeaders?: Record<string, string>;
}

export interface S3AudioSource {
  Type: "S3";
  BucketName: string;
  Key: string;
}

export interface Action {
  Type: string;
  Parameters: Record<string, any>;
}

export interface ActionData {
  Type: string;
  Parameters: Record<string, any>;
  ReceivedDigits?: string;
  ErrorType?: string;
  ErrorMessage?: string;
}

export interface PstnEvent {
  SchemaVersion: "1.0";
  Sequence: number;
  InvocationEventType: InvocationEventType;
  ActionData?: ActionData;
  CallDetails: {
    TransactionId: string;
    AwsAccountId: string;
    AwsRegion: string;
    SipMediaApplicationId: string;
    Participants: Participant[];
    TransactionAttributes?: Record<string, string>;
  };
}

export interface PstnResponse {
  SchemaVersion: "1.0";
  Actions: Action[];
  TransactionAttributes?: Record<string, string>;
}
