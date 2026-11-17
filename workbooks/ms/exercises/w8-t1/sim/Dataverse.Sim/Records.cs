using Microsoft.Xrm.Sdk;

namespace Dataverse.Sim;

/// <summary>Shape of a plugintracelog row (subset).</summary>
public sealed class TraceRecord
{
    public string TypeName { get; set; } = "";
    public string MessageName { get; set; } = "";
    public string PrimaryEntity { get; set; } = "";
    public int Depth { get; set; }
    public int Mode { get; set; }                 // 0 synchronous, 1 asynchronous
    public int Stage { get; set; }
    public int OperationType { get; set; } = 1;   // 1 = plug-in
    public Guid CorrelationId { get; set; }
    public Guid RequestId { get; set; }
    public DateTime CreatedOn { get; set; }
    public DateTime PerformanceExecutionStartTime { get; set; }
    public int PerformanceExecutionDuration { get; set; }  // ms
    public string MessageBlock { get; set; } = "";
    public string? ExceptionDetails { get; set; }
}

/// <summary>An IOrganizationService call recorded by the simulator.</summary>
public sealed class CallRecord
{
    public string Message { get; set; } = "";
    public string Entity { get; set; } = "";
    public Guid Id { get; set; }
    public int Depth { get; set; }               // depth of the operation this call starts
    public string? CallerPluginType { get; set; } // null = client call
    public int CallerStage { get; set; }
    public Guid? CallerRecordId { get; set; }
    public IReadOnlyCollection<string> Attributes { get; set; } = Array.Empty<string>();
}

/// <summary>Fault surfaced to the caller, shaped like an OrganizationServiceFault.</summary>
public sealed class DataverseFault : Exception
{
    public int ErrorCode { get; }
    public string HexCode => "0x" + ErrorCode.ToString("x8");
    public DataverseFault(int code, string message, Exception? inner = null) : base(message, inner) => ErrorCode = code;

    public const int SdkCorrelationTokenDepthTooHigh = unchecked((int)0x80044182);
    public const string LoopMessage = "This workflow job was canceled because the workflow that started it included an infinite loop. Correct the workflow logic and try again. For information about workflow logic, see Help.";
    public const int IsvAborted = unchecked((int)0x80040265);
    public const int IsvUnexpected = unchecked((int)0x80040224);
}
