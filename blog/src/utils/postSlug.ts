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
