export const CACHE_TAGS = {
  LOCAL_VIDEOS: "videos:local",
  DRIVE_VIDEOS: "videos:drive",
  RECENT_VIDEOS: "videos:recent",
  DRIVE_AUTH: "drive:auth",
} as const;

export const CACHE_TAG_SETS = {
  LOCAL_MUTATION: [CACHE_TAGS.LOCAL_VIDEOS, CACHE_TAGS.RECENT_VIDEOS],
  DRIVE_MUTATION: [CACHE_TAGS.DRIVE_VIDEOS],
} as const;
