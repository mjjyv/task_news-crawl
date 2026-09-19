import React from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getArticleDetail } from "@/lib/api";
import { Breadcrumb } from "@/components/Breadcrumb";
import { ArticleReaderView } from "@/components/ArticleReaderView";

interface ArticlePageProps {
  params: {
    id: string;
  };
}

export async function generateMetadata({
  params,
}: ArticlePageProps): Promise<Metadata> {
  try {
    const article = await getArticleDetail(params.id);
    return {
      title: `${article.title} | VnExpress Reader`,
      description: article.description || undefined,
      openGraph: {
        title: article.title,
        description: article.description || undefined,
        images: article.thumbnail_url ? [article.thumbnail_url] : [],
      },
    };
  } catch {
    return {
      title: "Bài viết | VnExpress Reader",
    };
  }
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  let article;
  try {
    article = await getArticleDetail(params.id);
  } catch (err) {
    console.error(`Article [${params.id}] not found:`, err);
    notFound();
  }

  const breadcrumbItems = [];
  if (article.category) {
    breadcrumbItems.push({
      label: article.category.name,
      href: `/category/${article.category.slug}`,
    });
  }
  breadcrumbItems.push({
    label: article.title,
  });

  return (
    <div className="space-y-4">
      {/* Breadcrumbs */}
      <Breadcrumb items={breadcrumbItems} />

      {/* Reader View */}
      <ArticleReaderView article={article} />
    </div>
  );
}
