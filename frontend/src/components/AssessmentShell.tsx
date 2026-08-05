import Link from "next/link";
import type { ReactNode } from "react";

import { AssessmentProgress } from "./AssessmentProgress";

interface Props {
  currentStep: 1 | 2 | 3 | 4;
  title: string;
  description: string;
  children: ReactNode;
}

export function AssessmentShell({ currentStep, title, description, children }: Props) {
  return (
    <main className="min-h-screen bg-sand px-4 py-6 sm:py-10">
      <div className="mx-auto max-w-3xl">
        <Link href="/" className="mb-6 inline-flex font-bold text-ink hover:text-leaf">
          CertifyLK
        </Link>
        <section className="rounded-3xl border border-emerald-100 bg-white p-5 shadow-card sm:p-9">
          <AssessmentProgress currentStep={currentStep} />
          <header className="mb-8 mt-7">
            <h1 className="text-3xl font-bold tracking-tight text-ink">{title}</h1>
            <p className="mt-3 max-w-2xl leading-7 text-slate-600">{description}</p>
          </header>
          {children}
        </section>
      </div>
    </main>
  );
}
