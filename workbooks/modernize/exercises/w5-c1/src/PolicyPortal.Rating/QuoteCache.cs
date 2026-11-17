using System.IO;
using System.Runtime.Serialization.Formatters.Binary;

namespace PolicyPortal.Rating
{
    /// <summary>
    /// Disk cache of issued quotes so the portal can re-display a quote for 30 days without re-rating.
    /// One file per quote in the cache directory.
    /// </summary>
    public sealed class QuoteCache
    {
        private readonly string dir;

        public QuoteCache(string dir)
        {
            this.dir = dir;
            Directory.CreateDirectory(dir);
        }

        public void Save(Quote quote)
        {
            using (FileStream fs = File.Create(Path.Combine(dir, quote.QuoteId + ".bin")))
            {
                new BinaryFormatter().Serialize(fs, quote);
            }
        }

        /// <summary>The cached quote, or null when there is none.</summary>
        public Quote TryLoad(string quoteId)
        {
            string path = Path.Combine(dir, quoteId + ".bin");
            if (!File.Exists(path))
            {
                return null;
            }
            using (FileStream fs = File.OpenRead(path))
            {
                return (Quote)new BinaryFormatter().Deserialize(fs);
            }
        }
    }
}
