using System;
using System.Collections.Generic;

namespace PolicyPortal.Rating
{
    /// <summary>
    /// Underwriter notes arrive as free text with tagged lines, e.g. "UW: approved" or "REF: inspection due".
    /// The portal shows the tags as separate fields; untagged lines are ignored.
    /// </summary>
    public static class PolicyNoteParser
    {
        public static IDictionary<string, string> Parse(string text)
        {
            var tags = new Dictionary<string, string>(StringComparer.Ordinal);
            int start = 0;
            while (start < text.Length)
            {
                // Ordinal: with ICU (.NET 5+) a culture-sensitive IndexOf("\n") does not match the \n inside "\r\n".
                int end = text.IndexOf('\n', start);
                if (end < 0)
                {
                    end = text.Length;
                }
                string line = text.Substring(start, end - start).TrimEnd('\r').Trim();
                int colon = line.IndexOf(':');
                if (colon > 0)
                {
                    string tag = line.Substring(0, colon).Trim().ToUpperInvariant();
                    if (tag.Length <= 5 && !tags.ContainsKey(tag))
                    {
                        tags[tag] = line.Substring(colon + 1).Trim();
                    }
                }
                start = end + 1;
            }
            return tags;
        }
    }
}
