export function DisclaimerCard({ text }: { text?: string }) {
  return (
    <aside className="rounded-2xl border border-amber-300 bg-amber-50 p-5 text-sm leading-6 text-amber-950">
      <p className="font-bold">Readiness guidance, not certification</p>
      <p className="mt-1">{text ?? "CertifyLK does not issue, guarantee, or replace SLS certification or an official inspection."}</p>
    </aside>
  );
}
