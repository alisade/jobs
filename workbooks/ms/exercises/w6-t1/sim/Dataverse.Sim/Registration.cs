using System.Text.Json;
using System.Text.Json.Serialization;

namespace Dataverse.Sim;

/// <summary>Simplified mirror of an sdkmessageprocessingstepimage row.</summary>
public sealed class ImageRegistration
{
    public string Type { get; set; } = "";        // PreImage | PostImage
    public string Alias { get; set; } = "";
    public List<string> Attributes { get; set; } = new();  // empty = all columns (the PRT default)
}

/// <summary>Simplified mirror of an sdkmessageprocessingstep row.</summary>
public sealed class StepRegistration
{
    public string Name { get; set; } = "";
    public string PluginType { get; set; } = "";
    public string Message { get; set; } = "";
    public string PrimaryEntity { get; set; } = "";
    public int Stage { get; set; }                  // 10 PreValidation, 20 PreOperation, 40 PostOperation
    public string Mode { get; set; } = "Synchronous";
    public int Rank { get; set; } = 1;
    public bool Enabled { get; set; } = true;
    public List<string> FilteringAttributes { get; set; } = new();
    public List<ImageRegistration> Images { get; set; } = new();
    public string? UnsecureConfig { get; set; }

    [JsonIgnore] public bool IsAsync => string.Equals(Mode, "Asynchronous", StringComparison.OrdinalIgnoreCase);
}

public sealed class RegistrationFile
{
    public string Assembly { get; set; } = "";
    public List<StepRegistration> Steps { get; set; } = new();

    public static RegistrationFile Load(string path)
    {
        var opts = new JsonSerializerOptions { PropertyNameCaseInsensitive = true, ReadCommentHandling = JsonCommentHandling.Skip, AllowTrailingCommas = true };
        return JsonSerializer.Deserialize<RegistrationFile>(File.ReadAllText(path), opts)
               ?? throw new InvalidOperationException("Empty registration file: " + path);
    }

    /// <summary>Rules the Plug-in Registration Tool / platform would enforce.</summary>
    public List<string> Validate(string primaryKeySuffix = "id")
    {
        var errors = new List<string>();
        foreach (var s in Steps)
        {
            if (s.Stage != 10 && s.Stage != 20 && s.Stage != 40)
                errors.Add($"{s.Name}: stage {s.Stage} is not a registrable stage (10, 20, 40).");
            if (s.IsAsync && s.Stage != 40)
                errors.Add($"{s.Name}: asynchronous steps can only be registered on PostOperation (40).");
            if (!string.Equals(s.Mode, "Synchronous", StringComparison.OrdinalIgnoreCase) && !s.IsAsync)
                errors.Add($"{s.Name}: mode must be Synchronous or Asynchronous.");
            if (s.FilteringAttributes.Count > 0 && !string.Equals(s.Message, "Update", StringComparison.OrdinalIgnoreCase))
                errors.Add($"{s.Name}: filtering attributes only apply to Update.");
            if (s.FilteringAttributes.Any(a => a.Equals(s.PrimaryEntity + primaryKeySuffix, StringComparison.OrdinalIgnoreCase)))
                errors.Add($"{s.Name}: the primary key is always in an Update and negates the filtering attributes.");
            foreach (var img in s.Images)
            {
                var t = img.Type.ToLowerInvariant();
                if (t != "preimage" && t != "postimage") errors.Add($"{s.Name}: image type '{img.Type}' is invalid.");
                if (t == "preimage" && s.Message.Equals("Create", StringComparison.OrdinalIgnoreCase))
                    errors.Add($"{s.Name}: Create has no pre-image (the row does not exist yet).");
                if (t == "postimage" && s.Stage != 40)
                    errors.Add($"{s.Name}: post-images are only available on PostOperation (40).");
                if (string.IsNullOrWhiteSpace(img.Alias)) errors.Add($"{s.Name}: image alias is required.");
            }
        }
        return errors;
    }
}
