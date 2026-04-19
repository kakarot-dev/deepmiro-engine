/**
 * Archetype → color + label mapping.
 *
 * Node colors in the GraphPanel are keyed by the agent's entity_type
 * from the OASIS profile. Keep this list aligned with DeepMiro's
 * common ontology outputs.
 */

export interface Archetype {
  label: string;
  color: string;
  description?: string;
}

const ARCHETYPE_MAP: Record<string, Archetype> = {
  TechCEO: { label: "Tech CEO", color: "#2dd4bf" },
  TechExecutive: { label: "Tech Exec", color: "#2dd4bf" },
  TechBillionaire: { label: "Tech Billionaire", color: "#2dd4bf" },
  PlatformCompany: { label: "Platform", color: "#818cf8" },
  PlatformCeo: { label: "Platform CEO", color: "#2dd4bf" },
  PlatformModerator: { label: "Moderator", color: "#f472b6" },

  Journalist: { label: "Journalist", color: "#fb923c" },
  TechJournalist: { label: "Tech Journalist", color: "#fb923c" },
  MediaPersonality: { label: "Media", color: "#fb923c" },
  PoliticalCommentator: { label: "Commentator", color: "#fb923c" },

  Politician: { label: "Politician", color: "#c084fc" },
  GovernmentOfficial: { label: "Gov't Official", color: "#c084fc" },
  RegulatoryBody: { label: "Regulator", color: "#c084fc" },

  AdvocacyGroup: { label: "Advocacy", color: "#4ade80" },
  DigitalRightsOrganization: { label: "Digital Rights", color: "#4ade80" },
  CivilLibertiesGroup: { label: "Civil Rights", color: "#4ade80" },

  Corporation: { label: "Corporation", color: "#facc15" },
  Company: { label: "Company", color: "#facc15" },
  Brand: { label: "Brand", color: "#facc15" },
  Advertiser: { label: "Advertiser", color: "#facc15" },

  AppDeveloper: { label: "Developer", color: "#a3e635" },
  Developer: { label: "Developer", color: "#a3e635" },

  AcademicResearcher: { label: "Researcher", color: "#7dd3fc" },
  Scientist: { label: "Scientist", color: "#7dd3fc" },
  Professor: { label: "Professor", color: "#7dd3fc" },

  Subreddit: { label: "Subreddit", color: "#f472b6" },
  Community: { label: "Community", color: "#f472b6" },
  AlternativePlatform: { label: "Alt Platform", color: "#f472b6" },

  VentureCapitalist: { label: "VC", color: "#facc15" },
  FinancialAnalyst: { label: "Analyst", color: "#facc15" },

  Student: { label: "Student", color: "#cbd5e1" },
  Person: { label: "Person", color: "#cbd5e1" },
  PowerUser: { label: "Power User", color: "#f472b6" },
  ContentCreator: { label: "Creator", color: "#fb923c" },
  RedditCoFounder: { label: "Co-founder", color: "#2dd4bf" },
};

const DEFAULT_ARCHETYPE: Archetype = {
  label: "Other",
  color: "#cbd5e1",
};

export function resolveArchetype(entityType?: string): Archetype {
  if (!entityType) return DEFAULT_ARCHETYPE;
  // Try exact match first, then case-insensitive, then substring fallback.
  if (ARCHETYPE_MAP[entityType]) return ARCHETYPE_MAP[entityType];
  const lower = entityType.toLowerCase();
  for (const [key, value] of Object.entries(ARCHETYPE_MAP)) {
    if (key.toLowerCase() === lower) return value;
  }
  for (const [key, value] of Object.entries(ARCHETYPE_MAP)) {
    if (lower.includes(key.toLowerCase()) || key.toLowerCase().includes(lower)) {
      return value;
    }
  }
  return DEFAULT_ARCHETYPE;
}
