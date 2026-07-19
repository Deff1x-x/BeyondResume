export type RoadmapPriority = "high" | "medium" | "low";

export type RoadmapItem = {
  id: string;
  title: string;
  reason: string;
  priority: RoadmapPriority;
  missing_skills: string[];
  related_skills: string[];
};

export type RoadmapResponse = {
  items: RoadmapItem[];
};
