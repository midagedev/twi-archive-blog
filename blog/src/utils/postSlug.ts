import type { CollectionEntry } from 'astro:content';

type BlogPostLike = Pick<CollectionEntry<'blog'>, 'id' | 'data'>;

const TWEET_ID_REGEX = /\/status\/(\d+)/;

const pad2 = (value: number) => String(value).padStart(2, '0');

const formatDateForSlug = (date: Date) => {
	const year = date.getUTCFullYear();
	const month = pad2(date.getUTCMonth() + 1);
	const day = pad2(date.getUTCDate());
	return `${year}${month}${day}`;
};

const extractTweetId = (url?: string) => url?.match(TWEET_ID_REGEX)?.[1];

export const getPostSlug = (post: BlogPostLike) => {
	const dateSlug = formatDateForSlug(post.data.pubDate);
	const tweetId = extractTweetId(post.data.originalTweetUrl);

	if (tweetId) {
		return `${dateSlug}-${tweetId}`;
	}

	const fallback = post.id.replace(/^\d{8}-/, '');
	return `${dateSlug}-${fallback}`;
};

export const getPostUrl = (post: BlogPostLike) => `/blog/${getPostSlug(post)}/`;

// 트윗 노트는 title이 본문 발췌라 description과 중복되기 쉽다.
// 중복이면 null을 반환해 카드/목록에서 설명 줄을 생략한다.
export const dedupeDescription = (title: string, description?: string) => {
	if (!description) return null;
	const stem = title.replace(/(\.\.\.|…)\s*$/, '').replace(/\s+/g, ' ').trim();
	const desc = description.replace(/\s+/g, ' ').trim();
	if (stem.length >= 12 && desc.includes(stem.slice(0, Math.min(stem.length, 40)))) return null;
	return description;
};
