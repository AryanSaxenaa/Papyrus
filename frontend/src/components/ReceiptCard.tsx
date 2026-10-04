import type { SerpApiReceipt } from "../types";

type Props = {
  receipt: SerpApiReceipt;
};

export function ReceiptCard({ receipt }: Props) {
  const archiveUrl = receipt.json_endpoint;
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/80 p-3 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="font-audit font-medium text-zinc-800">{receipt.engine}</span>
        <span className="text-zinc-500">
          {receipt.cache_hit ? "cached · 0 credits" : `${receipt.credits} credit(s)`}
        </span>
      </div>
      {receipt.search_metadata_id && (
        <p className="mt-2 font-audit text-[10px] text-zinc-500">
          search_metadata.id: <span className="text-zinc-800">{receipt.search_metadata_id}</span>
        </p>
      )}
      <pre className="mt-2 max-h-24 overflow-auto rounded bg-white p-2 font-audit text-[10px] text-zinc-600">
        {JSON.stringify(receipt.params, null, 2)}
      </pre>
      {archiveUrl && (
        <a
          href={archiveUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-2 inline-block text-[11px] font-medium text-sky-700 underline-offset-2 hover:underline"
        >
          Verify now (SerpApi archive)
        </a>
      )}
    </div>
  );
}
