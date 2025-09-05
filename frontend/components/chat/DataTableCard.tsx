"use client";

export default function DataTableCard({
  columns,
  rows,
}: {
  columns: string[];
  rows: (string | number)[][];
}) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-left text-white/80">
          {columns.map((c) => (
            <th key={c} className="py-2 pr-4">{c}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className="border-t border-white/10">
            {r.map((cell, j) => (
              <td key={j} className="py-2 pr-4 text-white/80">
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
