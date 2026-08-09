import Image from "next/image";
import Link from "next/link";

interface SiteLogoProps {
  href?: string;
  className?: string;
  tone?: "default" | "onDark";
}

export function SiteLogo({ href = "/", className = "", tone = "default" }: SiteLogoProps) {
  const wordmark = tone === "onDark" ? "text-white" : "text-ink";

  const content = (
    <>
      <span
        aria-hidden="true"
        className="relative h-9 w-9 shrink-0 overflow-hidden rounded-xl shadow-soft transition-transform group-hover:scale-105"
      >
        <Image
          src="/logo.png"
          alt=""
          width={36}
          height={36}
          className="h-full w-full object-cover"
          priority
        />
      </span>
      <span className={`font-display text-lg font-bold tracking-tight ${wordmark}`}>
        Certify<span className="text-leaf">LK</span>
      </span>
    </>
  );

  if (href) {
    return (
      <Link href={href} className={`group inline-flex items-center gap-2.5 ${className}`}>
        {content}
      </Link>
    );
  }

  return <span className={`inline-flex items-center gap-2.5 ${className}`}>{content}</span>;
}
