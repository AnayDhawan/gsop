import Image from "next/image";
import { groupByDataset, type Evidence } from "@/lib/evidence";

type Props = { evidence: Evidence | null; chip: { src: string; credit: string | null } | null; radiusClaim: (r: string) => string };

/** Optional section (C8). The page passes null for `evidence` when the file is absent, and nothing is rendered. */
export default function MeasuredEvidence({ evidence, chip, radiusClaim }: Props) {
  if (evidence === null) return null;
  return (
    <section className="space-y-3" aria-labelledby="evidence">
      <h3 id="evidence" className="text-lg">
        Measured evidence
      </h3>
      <p className="text-secondary-foreground">
        Open Earth data summarised over a circle around the listed coordinates. These describe the place around the coordinates, not whether it is a good analog.
        {evidence.approximateOnly ? " The coordinates for this site are approximate, so only the larger circle is shown, and its values carry that caveat." : ""}
      </p>
      {chip && (
        <figure className="space-y-1">
          <Image src={chip.src} alt="Satellite image chip around the listed coordinates" width={640} height={640} unoptimized className="h-auto max-w-sm border border-border" />
          {chip.credit && <figcaption className="text-xs text-muted-foreground">{chip.credit}</figcaption>}
        </figure>
      )}
      {evidence.rows.length === 0 ? (
        <p className="text-muted-foreground">not measured</p>
      ) : (
        groupByDataset(evidence.rows).map(([dataset, rows]) => (
          <div key={dataset} className="space-y-1">
            <h4 className="gsop-label">{dataset.replace(/_/g, " ")}</h4>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <caption className="sr-only">Measurements from {dataset}</caption>
                <thead>
                  <tr className="border-b border-border">
                    <th scope="col" className="py-2 pr-4 font-medium">Variable</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Statistic</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Radius (km)</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Value</th>
                    <th scope="col" className="py-2 pr-4 font-medium">Product and version</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r, i) => (
                    <tr key={`${r.variable}-${r.stat}-${r.radius}-${i}`} className="border-b border-border align-top">
                      <th scope="row" className="py-2 pr-4 font-medium">
                        {r.variable.replace(/_/g, " ")}
                      </th>
                      <td className="py-2 pr-4">{r.stat.replace(/_/g, " ")}</td>
                      <td className="py-2 pr-4">{radiusClaim(r.radius)}</td>
                      <td className={`py-2 pr-4 ${r.value === "not measured" ? "text-muted-foreground" : ""}`}>
                        {r.value}
                        {r.value !== "not measured" && r.units ? ` ${r.units}` : ""}
                        {r.value === "not measured" && r.note ? <span className="block text-xs">{r.note.replace(/_/g, " ")}</span> : null}
                      </td>
                      <td className="py-2 pr-4">{r.product}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </section>
  );
}
