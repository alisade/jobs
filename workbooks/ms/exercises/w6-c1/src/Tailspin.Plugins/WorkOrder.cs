using System.Collections.Generic;

namespace Tailspin.Plugins
{
    /// <summary>
    /// Schema names and choice values for the contoso_workorder table (provided; do not change).
    /// </summary>
    public static class WorkOrder
    {
        public const string EntityName = "contoso_workorder";
        public const string PrimaryKey = "contoso_workorderid";

        public const string Status = "contoso_status";                 // Choice (OptionSetValue)
        public const string ActualStart = "contoso_actualstart";       // Date and time (UTC)
        public const string CompletedOn = "contoso_completedon";       // Date and time (UTC)
        public const string StatusChangedOn = "contoso_statuschangedon"; // Date and time (UTC)
        public const string DurationMinutes = "contoso_durationminutes"; // Whole number
        public const string ResolutionNotes = "contoso_resolutionnotes"; // Multiline text

        public const int New = 100000000;
        public const int Scheduled = 100000001;
        public const int InProgress = 100000002;
        public const int OnHold = 100000003;
        public const int Completed = 100000004;
        public const int Cancelled = 100000005;

        /// <summary>Labels used in user-facing error messages.</summary>
        public static readonly IDictionary<int, string> Labels = new Dictionary<int, string>
        {
            { New, "New" },
            { Scheduled, "Scheduled" },
            { InProgress, "In Progress" },
            { OnHold, "On Hold" },
            { Completed, "Completed" },
            { Cancelled, "Cancelled" },
        };
    }
}
