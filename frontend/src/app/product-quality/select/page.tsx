"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Boxes, Check, PackageSearch } from "lucide-react";

import { ErrorAlert } from "@/components/ErrorAlert";
import { FlowHeader, FlowSteps } from "@/components/FlowHeader";
import { Spinner } from "@/components/LoadingState";
import { api, ApiError } from "@/lib/api";
import type { Category, Product } from "@/types";

const STEPS = ["Choose product", "Business profile", "Certificates"];

export default function SelectProductPage() {
  const router = useRouter();
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .listCategories()
      .then((cats) => {
        if (!cancelled) {
          setCategories(cats);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load categories.");
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onCategorySelect(cat: Category) {
    setSelectedCategory(cat);
    setSelectedProduct(null);
    setProducts([]);
    try {
      const prods = await api.listProducts(cat.id);
      setProducts(prods);
    } catch {
      setError("Failed to load products for this category.");
    }
  }

  async function onContinue() {
    if (!selectedProduct) return;
    setCreating(true);
    setError(null);
    try {
      const { id } = await api.createAssessment();
      router.push(`/product-quality/${id}/business-profile?product=${selectedProduct.slug}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to start assessment. Please try again.",
      );
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-surface">
      <FlowHeader trailing={<FlowSteps steps={STEPS} current={1} tone="leaf" />} />

      <main className="mx-auto max-w-4xl space-y-8 px-4 py-10 sm:px-6">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-leaf/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-leaf-dark">
            Track 1 · Product Quality
          </span>
          <h1 className="section-title mt-3">What product do you manufacture?</h1>
          <p className="section-lead">
            Select your product category, then your specific product. We&apos;ll use this to find the
            right certification schemes and requirements for you.
          </p>
        </div>

        {error ? <ErrorAlert message={error} /> : null}

        {/* Category grid */}
        <section>
          <div className="mb-3 flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-leaf text-xs font-bold text-white">
              1
            </span>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate">
              Select category
            </h2>
          </div>
          {loading ? (
            <div className="flex items-center gap-3 text-sm text-slate">
              <Spinner className="text-leaf" />
              Loading categories…
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {categories.map((cat) => {
                const active = selectedCategory?.id === cat.id;
                return (
                  <button
                    key={cat.id}
                    id={`cat-${cat.slug}`}
                    type="button"
                    onClick={() => void onCategorySelect(cat)}
                    aria-pressed={active}
                    className={`flex flex-col rounded-2xl border p-5 text-left transition-all ${
                      active
                        ? "border-leaf bg-leaf/5 shadow-card"
                        : "border-slate-200 bg-white hover:border-leaf/40 hover:shadow-soft"
                    }`}
                  >
                    <span
                      className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl ${
                        active ? "bg-leaf text-white" : "bg-slate-100 text-slate-500"
                      }`}
                    >
                      <Boxes className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <span className="text-sm font-semibold text-ink">{cat.name}</span>
                    {cat.description ? (
                      <span className="mt-1 line-clamp-2 text-xs text-slate">{cat.description}</span>
                    ) : null}
                  </button>
                );
              })}
            </div>
          )}
        </section>

        {/* Product list */}
        {selectedCategory ? (
          <section>
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-leaf text-xs font-bold text-white">
                2
              </span>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate">
                Select product
              </h2>
            </div>
            {products.length === 0 ? (
              <div className="flex items-center gap-3 text-sm text-slate">
                <Spinner className="text-leaf" />
                Loading products…
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                {products.map((prod) => {
                  const active = selectedProduct?.id === prod.id;
                  return (
                    <button
                      key={prod.id}
                      id={`prod-${prod.slug}`}
                      type="button"
                      onClick={() => setSelectedProduct(prod)}
                      aria-pressed={active}
                      className={`relative flex flex-col rounded-2xl border p-5 text-left transition-all ${
                        active
                          ? "border-leaf bg-leaf/5 shadow-card"
                          : "border-slate-200 bg-white hover:border-leaf/40 hover:shadow-soft"
                      }`}
                    >
                      {active ? (
                        <span className="absolute right-4 top-4 inline-flex h-5 w-5 items-center justify-center rounded-full bg-leaf text-white">
                          <Check className="h-3 w-3" aria-hidden="true" />
                        </span>
                      ) : null}
                      <span
                        className={`mb-3 inline-flex h-9 w-9 items-center justify-center rounded-xl ${
                          active ? "bg-leaf text-white" : "bg-slate-100 text-slate-500"
                        }`}
                      >
                        <PackageSearch className="h-4 w-4" aria-hidden="true" />
                      </span>
                      <span className="text-sm font-semibold text-ink">{prod.name}</span>
                      {prod.description ? (
                        <span className="mt-1 line-clamp-3 text-xs text-slate">
                          {prod.description}
                        </span>
                      ) : null}
                    </button>
                  );
                })}
              </div>
            )}
          </section>
        ) : null}

        <div className="flex justify-end pt-2">
          <button
            id="select-product-continue"
            type="button"
            disabled={!selectedProduct || creating}
            onClick={() => void onContinue()}
            className="btn-primary px-8"
          >
            {creating ? (
              <>
                <Spinner className="text-white" />
                Starting…
              </>
            ) : (
              <>
                Continue
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </>
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
