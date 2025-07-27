import React from "react";
import { useEffect, useState } from "react";

// Types -------------------------------------------------------------
interface Recommendation {
  priority: number;
  title: string;
  detail: string;
}
interface Drill {
  name: string;
  goal: string;
  duration_minutes?: number;
}

interface GenericCoach {
  overview: string;
  strengths?: string[];
  weaknesses?: string[];
  recommendations?: Recommendation[];
  drills?: Drill[];
  references?: string[];
  // LoL extras
  lane?: string;
  champion_tips?: string[];
  objective_focus?: string;
  item_build?: string[];
  // PUBG extras
  preferred_map?: string;
  drop_spots?: string[];
  weapon_loadout?: string[];
  item?: string[];
  rotation_strategy?: string;
  engagement_style?: string;
  mode_extras?: Record<string, unknown>;
  [k: string]: unknown;
}

interface Props {
  data: GenericCoach;
  game?: "lol" | "pubg" | "general";
}

const ListBlock: React.FC<{ title: string; items?: string[] }> = ({ title, items }) => {
  if (!items || items.length === 0) return null;
  return (
    <div className="mb-2">
      <h4 className="font-semibold mb-1 text-xs text-muted uppercase">{title}</h4>
      <ul className="list-disc list-inside space-y-0.5 text-sm">
        {items.map((t) => (
          <li key={t}>{t}</li>
        ))}
      </ul>
    </div>
  );
};

const CoachStructuredView: React.FC<Props> = ({ data, game = "general" }) => {
  const [imageMap, setImageMap] = useState<Record<string, string>>({});

  useEffect(() => {
    const toFetch: { game: string; asset_type: string; key: string }[] = [];
    if (game === "lol") {
      (data.champion_tips || []).forEach((c) => toFetch.push({ game: "lol", asset_type: "champion", key: c }));
      (data.item_build || []).forEach((i) => toFetch.push({ game: "lol", asset_type: "item", key: i }));
    }
    if (game === "pubg") {
      (data.weapon_loadout || []).forEach((w) => toFetch.push({ game: "pubg", asset_type: "weapon", key: w }));
      (data.item || []).forEach((it: string) => toFetch.push({ game: "pubg", asset_type: "item", key: it }));
    }
    if (toFetch.length === 0) return;

    fetch("/api/assets/batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ items: toFetch }),
    })
      .then((r) => r.json())
      .then((json) => setImageMap(json.urls || {}))
      .catch(() => {});
  }, [data, game]);

  return (
    <div className="flex flex-col gap-3">
      {/* Overview */}
      {data.overview && <p className="text-sm whitespace-pre-wrap">{data.overview}</p>}

      {/* Strengths / Weaknesses */}
      <div className="grid grid-cols-2 gap-4">
        <ListBlock title="Strengths" items={data.strengths as string[]} />
        <ListBlock title="Weaknesses" items={data.weaknesses as string[]} />
      </div>

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div>
          <h4 className="font-semibold mb-1 text-xs text-muted uppercase">Prioritized Actions</h4>
          <ol className="space-y-1 text-sm">
            {data.recommendations
              .sort((a, b) => a.priority - b.priority)
              .map((rec) => (
                <li key={rec.title} className="border-l-2 border-primary pl-2">
                  <span className="font-medium">{rec.title}</span>: {rec.detail}
                </li>
              ))}
          </ol>
        </div>
      )}

      {/* Drills */}
      {data.drills && data.drills.length > 0 && (
        <div>
          <h4 className="font-semibold mb-1 text-xs text-muted uppercase">Practice Drills</h4>
          <ul className="space-y-1 text-sm">
            {data.drills.map((d) => (
              <li key={d.name} className="border rounded p-2">
                <span className="font-medium">{d.name}</span> - {d.goal}
                {d.duration_minutes && (
                  <span className="ml-1 text-muted text-xs">({d.duration_minutes}m)</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Game-specific extras */}
      {game === "lol" && (
        <>
          {data.lane && (
            <p className="text-sm">
              <span className="font-semibold">Lane:</span> {data.lane}
            </p>
          )}
          {data.champion_tips && data.champion_tips.length > 0 && (
            <div className="mb-2">
              <h4 className="font-semibold mb-1 text-xs text-muted uppercase">Champion Tips</h4>
              <div className="flex flex-wrap gap-2">
                {(data.champion_tips as string[]).map((c) => (
                  <div key={c} className="flex flex-col items-center text-xs w-16">
                    <img
                      src={imageMap[`lol:champion:${c}`]}
                      alt={c}
                      className="rounded"
                    />
                    <span>{c}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {data.objective_focus && (
            <p className="text-sm">
              <span className="font-semibold">Objective Focus:</span> {data.objective_focus}
            </p>
          )}
          {data.item_build && data.item_build.length > 0 && (
            <div className="mb-2">
              <h4 className="font-semibold mb-1 text-xs text-muted uppercase">Item Build</h4>
              <div className="flex flex-wrap gap-1">
                {(data.item_build as string[]).map((i) => (
                  <img
                    key={i}
                    src={imageMap[`lol:item:${i}`]}
                    alt={i}
                    className="h-10 w-10 rounded"
                  />
                ))}
              </div>
            </div>
          )}
          {data.mode_extras && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-muted">Extra Info</summary>
              <pre className="text-xs mt-1 bg-surface p-2 rounded max-h-48 overflow-auto">
                {JSON.stringify(data.mode_extras, null, 2)}
              </pre>
            </details>
          )}
        </>
      )}

      {game === "pubg" && (
        <>
          {data.preferred_map && (
            <p className="text-sm">
              <span className="font-semibold">Preferred Map:</span> {data.preferred_map}
            </p>
          )}
          <ListBlock title="Drop Spots" items={data.drop_spots as string[]} />
          {data.weapon_loadout && data.weapon_loadout.length > 0 && (
            <div className="mb-2">
              <h4 className="font-semibold mb-1 text-xs text-muted uppercase">Weapon Loadout</h4>
              <div className="flex flex-wrap gap-1">
                {(data.weapon_loadout as string[]).map((w) => (
                  <img
                    key={w}
                    src={imageMap[`pubg:weapon:${w}`]}
                    alt={w}
                    className="h-10 w-10 rounded"
                  />
                ))}
              </div>
            </div>
          )}

          {data.item && Array.isArray(data.item) && (
            <div className="mb-2">
              <h4 className="font-semibold mb-1 text-xs text-muted uppercase">Items</h4>
              <div className="flex flex-wrap gap-1">
                {data.item.map((it: string) => (
                  <img
                    key={it}
                    src={imageMap[`pubg:item:${it}`]}
                    alt={it}
                    className="h-8 w-8 rounded"
                  />
                ))}
              </div>
            </div>
          )}

          {data.mode_extras && (
            <details className="mt-2">
              <summary className="cursor-pointer text-xs text-muted">Extra Info</summary>
              <pre className="text-xs mt-1 bg-surface p-2 rounded max-h-48 overflow-auto">
                {JSON.stringify(data.mode_extras, null, 2)}
              </pre>
            </details>
          )}

          {data.rotation_strategy && (
            <p className="text-sm">
              <span className="font-semibold">Rotation Strategy:</span> {data.rotation_strategy}
            </p>
          )}
          {data.engagement_style && (
            <p className="text-sm">
              <span className="font-semibold">Engagement Style:</span> {data.engagement_style}
            </p>
          )}
        </>
      )}

      {/* References */}
      {data.references && data.references.length > 0 && (
        <div>
          <h4 className="font-semibold mb-1 text-xs text-muted uppercase">References</h4>
          <ul className="space-y-0.5 text-sm underline text-blue-500">
            {data.references.map((r) => (
              <li key={r}>
                <a href={r} target="_blank" rel="noopener noreferrer">
                  {r}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default CoachStructuredView; 