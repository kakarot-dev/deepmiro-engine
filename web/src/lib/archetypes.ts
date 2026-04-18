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
  TechCEO: { label: "Tech CEO", color: "var(--arch-tech)" },
  TechExecutive: { label: "Tech Exec", color: "var(--arch-tech)" },
  TechBillionaire: { label: "Tech Billionaire", color: "var(--arch-tech)" },
  PlatformCompany: { label: "Platform", color: "var(--arch-platform)" },
  PlatformCeo: { label: "Platform CEO", color: "var(--arch-tech)" },
  PlatformModerator: { label: "Moderator", color: "var(--arch-community)" },

  Journalist: { label: "Journalist", color: "var(--arch-media)" },
  TechJournalist: { label: "Tech Journalist", color: "var(--arch-media)" },
  MediaPersonality: { label: "Media", color: "var(--arch-media)" },
  PoliticalCommentator: { label: "Commentator", color: "var(--arch-media)" },

  Politician: { label: "Politician", color: "var(--arch-politician)" },
  GovernmentOfficial: { label: "Gov't Official", color: "var(--arch-politician)" },
  RegulatoryBody: { label: "Regulator", color: "var(--arch-politician)" },

  AdvocacyGroup: { label: "Advocacy", color: "var(--arch-activist)" },
  DigitalRightsOrganization: { label: "Digital Rights", color: "var(--arch-activist)" },
  CivilLibertiesGroup: { label: "Civil Rights", color: "var(--arch-activist)" },

  Corporation: { label: "Corporation", color: "var(--arch-business)" },
  Company: { label: "Company", color: "var(--arch-business)" },
  Brand: { label: "Brand", color: "var(--arch-business)" },
  Advertiser: { label: "Advertiser", color: "var(--arch-business)" },

  AppDeveloper: { label: "Developer", color: "var(--arch-developer)" },
  Developer: { label: "Developer", color: "var(--arch-developer)" },

  AcademicResearcher: { label: "Researcher", color: "var(--arch-researcher)" },
  Scientist: { label: "Scientist", color: "var(--arch-researcher)" },
  Professor: { label: "Professor", color: "var(--arch-researcher)" },

  Subreddit: { label: "Subreddit", color: "var(--arch-community)" },
  Community: { label: "Community", color: "var(--arch-community)" },
  AlternativePlatform: { label: "Alt Platform", color: "var(--arch-community)" },

  VentureCapitalist: { label: "VC", color: "var(--arch-business)" },
  FinancialAnalyst: { label: "Analyst", color: "var(--arch-business)" },

  Student: { label: "Student", color: "var(--arch-person)" },
  Person: { label: "Person", color: "var(--arch-person)" },
  PowerUser: { label: "Power User", color: "var(--arch-community)" },
  ContentCreator: { label: "Creator", color: "var(--arch-media)" },
  RedditCoFounder: { label: "Co-founder", color: "var(--arch-tech)" },
};

const DEFAULT_ARCHETYPE: Archetype = {
  label: "Other",
  color: "var(--arch-person)",
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
