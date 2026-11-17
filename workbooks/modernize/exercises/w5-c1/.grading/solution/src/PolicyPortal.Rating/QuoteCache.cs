using System.IO;
using System.Text.Json;

namespace PolicyPortal.Rating
{
    /// <summary>
    /// Disk cache of issued quotes so the portal can re-display a quote for 30 days without re-rating.
    /// One JSON file per quote ("{quoteId}.json", camelCase), the format the Java rating service also
    /// reads. The old binary serializer is gone: obsolete since .NET 5 and it throws from .NET 9 on, and it was
    /// never safe on files. Old ".bin" entries are treated as cache misses and expire on their own.
    /// </summary>
    public sealed class QuoteCache
    {
        private static readonly JsonSerializerOptions Json = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            WriteIndented = true,
        };

        private readonly string dir;

        public QuoteCache(string dir)
        {
            this.dir = dir;
            Directory.CreateDirectory(dir);
        }

        public void Save(Quote quote)
        {
            string path = Path.Combine(dir, quote.QuoteId + ".json");
            string tmp = path + ".tmp";
            File.WriteAllText(tmp, JsonSerializer.Serialize(quote, Json));
            File.Move(tmp, path, true);
        }

        /// <summary>The cached quote, or null when there is none.</summary>
        public Quote TryLoad(string quoteId)
        {
            string path = Path.Combine(dir, quoteId + ".json");
            if (!File.Exists(path))
            {
                return null;
            }
            return JsonSerializer.Deserialize<Quote>(File.ReadAllText(path), Json);
        }
    }
}
