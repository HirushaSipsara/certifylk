"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Category, Product } from "@/types";

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
    api.listCategories()
      .then((cats) => { if (!cancelled) { setCategories(cats); setLoading(false); } })
      .catch((err) => { if (!cancelled) { setError(err instanceof ApiError ? err.message : "Failed to load categories."); setLoading(false); } });
    return () => { cancelled = true; };
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
      // Create a new assessment to hold this session
      const { id } = await api.createAssessment();
      // Navigate to business profile page with the session and product
      router.push(
        `/product-quality/${id}/business-profile?product=${selectedProduct.slug}`
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start assessment. Please try again.");
      setCreating(false);
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#fffaf0] via-[#f0faf5] to-[#e8f5f0]">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-emerald-100 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <span className="text-2xl">🍃</span>
            <span className="font-bold text-emerald-800 text-lg">CertifyLK</span>
          </Link>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs font-bold">1</span>
            <span className="text-emerald-700 font-medium">Choose product</span>
            <span>→</span>
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 flex items-center justify-center text-xs font-bold">2</span>
            <span className="hidden sm:inline">Business profile</span>
            <span className="hidden sm:inline">→</span>
            <span className="w-6 h-6 rounded-full bg-gray-200 text-gray-400 items-center justify-center text-xs font-bold hidden sm:flex">3</span>
            <span className="hidden sm:inline">Certificates</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-emerald-900">
            What product do you manufacture?
          </h1>
          <p className="text-gray-500 mt-2 text-sm leading-relaxed">
            Select your product category, then your specific product. We&apos;ll use this to find the right
            certification schemes and requirements for you.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl p-4">
            {error}
          </div>
        )}

        {/* Category grid */}
        <section>
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Step 1 — Select category
          </h2>
          {loading ? (
            <div className="flex items-center gap-3 text-sm text-gray-400">
              <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
              Loading categories…
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  id={`cat-${cat.slug}`}
                  onClick={() => void onCategorySelect(cat)}
                  className={`text-left p-5 rounded-2xl border-2 transition-all ${
                    selectedCategory?.id === cat.id
                      ? "border-emerald-500 bg-emerald-50 shadow-md"
                      : "border-gray-200 bg-white hover:border-emerald-300 hover:shadow-sm"
                  }`}
                >
                  <div className="text-2xl mb-2">🏭</div>
                  <div className="font-semibold text-gray-800 text-sm">{cat.name}</div>
                  {cat.description && (
                    <div className="text-xs text-gray-400 mt-1 line-clamp-2">{cat.description}</div>
                  )}
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Product list */}
        {selectedCategory && (
          <section>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Step 2 — Select product
            </h2>
            {products.length === 0 ? (
              <div className="flex items-center gap-3 text-sm text-gray-400">
                <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                Loading products…
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {products.map((prod) => (
                  <button
                    key={prod.id}
                    id={`prod-${prod.slug}`}
                    onClick={() => setSelectedProduct(prod)}
                    className={`text-left p-5 rounded-2xl border-2 transition-all ${
                      selectedProduct?.id === prod.id
                        ? "border-emerald-500 bg-emerald-50 shadow-md"
                        : "border-gray-200 bg-white hover:border-emerald-300 hover:shadow-sm"
                    }`}
                  >
                    <div className="text-2xl mb-2">🍶</div>
                    <div className="font-semibold text-gray-800 text-sm">{prod.name}</div>
                    {prod.description && (
                      <div className="text-xs text-gray-400 mt-1 line-clamp-3">{prod.description}</div>
                    )}
                  </button>
                ))}
              </div>
            )}
          </section>
        )}

        {/* CTA */}
        <div className="flex justify-end pt-2">
          <button
            id="select-product-continue"
            disabled={!selectedProduct || creating}
            onClick={() => void onContinue()}
            className="bg-emerald-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-emerald-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {creating ? (
              <>
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Starting…
              </>
            ) : (
              "Continue →"
            )}
          </button>
        </div>
      </main>
    </div>
  );
}
