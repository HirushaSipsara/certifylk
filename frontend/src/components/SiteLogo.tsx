import Link from "next/link";

interface SiteLogoProps {
  href?: string;
  className?: string;
}

export function SiteLogo({ href = "/", className = "" }: SiteLogoProps) {
  const content = (
    <>
      <span
        aria-hidden="true"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-leaf text-sm font-bold text-white"
      >
        CL
      </span>
      <span className="font-semibold text-lg text-ink tracking-tight">CertifyLK</span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={`inline-flex items-center gap-2.5 group ${className}`}>
        {content}
      </Link>
    );
  }

  return <span className={`inline-flex items-center gap-2.5 ${className}`}>{content}</span>;
}
