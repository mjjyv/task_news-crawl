import {
  ArticleDetail,
  ArticleSummary,
  CategoryDetailResponse,
  CategoryTreeItem,
  CrawlerHealthResponse,
  CrawlTriggerRequest,
  CrawlTriggerResponse,
  PaginatedResponse,
  SearchResponse,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
  });

  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errData = await res.json();
      errorDetail = errData.detail || errData.error || errorDetail;
    } catch {
      // ignore json parse error
    }
    throw new Error(`API Error [${res.status}]: ${errorDetail}`);
  }

  return res.json() as Promise<T>;
}

export async function getCategories(tree = true): Promise<CategoryTreeItem[]> {
  return fetchJson<CategoryTreeItem[]>(`${API_BASE_URL}/categories?tree=${tree}`, {
    next: { revalidate: 60 },
  });
}

export async function getCategoryBySlug(slug: string): Promise<CategoryDetailResponse> {
  return fetchJson<CategoryDetailResponse>(`${API_BASE_URL}/categories/${slug}`, {
    next: { revalidate: 60 },
  });
}

export async function getArticles(params?: {
  category?: string;
  from_date?: string;
  to_date?: string;
  page?: number;
  page_size?: number;
  order?: "desc" | "asc";
}): Promise<PaginatedResponse<ArticleSummary>> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.from_date) query.set("from_date", params.from_date);
  if (params?.to_date) query.set("to_date", params.to_date);
  if (params?.page) query.set("page", params.page.toString());
  if (params?.page_size) query.set("page_size", params.page_size.toString());
  if (params?.order) query.set("order", params.order);

  const qs = query.toString();
  return fetchJson<PaginatedResponse<ArticleSummary>>(
    `${API_BASE_URL}/articles${qs ? `?${qs}` : ""}`,
    { next: { revalidate: 30 } }
  );
}

export async function getArticleDetail(id: number | string): Promise<ArticleDetail> {
  return fetchJson<ArticleDetail>(`${API_BASE_URL}/articles/${id}`, {
    next: { revalidate: 60 },
  });
}

export async function searchArticles(params: {
  q: string;
  category?: string;
  exact_accent?: boolean;
  page?: number;
  page_size?: number;
}): Promise<SearchResponse> {
  const query = new URLSearchParams();
  query.set("q", params.q);
  if (params.category) query.set("category", params.category);
  if (params.exact_accent !== undefined) {
    query.set("exact_accent", params.exact_accent.toString());
  }
  if (params.page) query.set("page", params.page.toString());
  if (params.page_size) query.set("page_size", params.page_size.toString());

  return fetchJson<SearchResponse>(`${API_BASE_URL}/search?${query.toString()}`);
}

export async function getCrawlerHealth(): Promise<CrawlerHealthResponse> {
  return fetchJson<CrawlerHealthResponse>(`${API_BASE_URL}/crawler/health`, {
    cache: "no-store",
  });
}

export async function triggerCrawl(
  payload: CrawlTriggerRequest
): Promise<CrawlTriggerResponse> {
  return fetchJson<CrawlTriggerResponse>(`${API_BASE_URL}/crawler/trigger`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
