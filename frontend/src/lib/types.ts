export interface CategoryShort {
  id: number;
  name: string;
  slug: string;
}

export interface CategoryBase {
  id: number;
  name: string;
  slug: string;
  origin_url: string;
  parent_id?: number | null;
  description?: string | null;
}

export interface CategoryTreeItem extends CategoryBase {
  children: CategoryTreeItem[];
  article_count: number;
}

export interface CategoryDetailResponse extends CategoryBase {
  parent?: CategoryBase | null;
  children: CategoryBase[];
  article_count: number;
}

export interface MediaItem {
  id: number;
  type: string; // 'image', 'video', 'audio'
  url: string;
  caption?: string | null;
  width?: number | null;
  height?: number | null;
}

export interface ArticleSummary {
  id: number;
  title: string;
  slug: string;
  description?: string | null;
  thumbnail_url?: string | null;
  author?: string | null;
  origin_url: string;
  published_at?: string | null;
  category?: CategoryShort | null;
  comment_count?: number;
}

export interface ArticleDetail {
  id: number;
  title: string;
  slug: string;
  description?: string | null;
  content_html: string;
  content_text: string;
  author?: string | null;
  thumbnail_url?: string | null;
  origin_url: string;
  published_at?: string | null;
  created_at?: string | null;
  category?: CategoryShort | null;
  comment_count?: number;
  media: MediaItem[];
  related_articles: ArticleSummary[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SearchResultItem {
  id: number;
  title: string;
  slug: string;
  description?: string | null;
  thumbnail_url?: string | null;
  author?: string | null;
  published_at?: string | null;
  category?: CategoryShort | null;
  score: number;
  comment_count?: number;
  snippet?: string | null;
}

export interface SearchResponse {
  query: string;
  exact_accent: boolean;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  items: SearchResultItem[];
}

export interface CrawlLogItem {
  id: number;
  crawler_type: string;
  target_url: string;
  status: string;
  articles_found: number;
  articles_new: number;
  error_message?: string | null;
  executed_at?: string | null;
}

export interface CrawlerHealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  database_connected: boolean;
  redis_connected: boolean;
  deduplicator_type: string;
  total_categories: number;
  total_articles: number;
  total_media: number;
  seen_ids_count: number;
  latest_logs: CrawlLogItem[];
}

export interface CrawlTriggerRequest {
  type: "rss" | "category";
  target: string;
  pages?: number;
  max_articles?: number;
}

export interface CrawlTriggerResponse {
  status: string;
  message: string;
  task_type: string;
  target: string;
}
