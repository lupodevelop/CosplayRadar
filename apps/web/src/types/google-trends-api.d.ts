// Types per google-trends-api (non ufficiali)
declare module 'google-trends-api' {
  interface TrendsOptions {
    keyword: string | string[];
    startTime?: Date;
    endTime?: Date;
    geo?: string;
    granularTimeUnit?: 'day' | 'week' | 'month';
    resolution?: 'COUNTRY' | 'REGION' | 'CITY' | 'DMA';
    timezone?: number;
    category?: number;
    property?: string;
  }

  interface RelatedQueriesOptions {
    keyword: string;
    startTime?: Date;
    endTime?: Date;
    geo?: string;
    category?: number;
    property?: string;
  }

  interface AutocompleteOptions {
    keyword: string;
    geo?: string;
  }

  export function interestOverTime(options: TrendsOptions): Promise<string>;
  export function interestByRegion(options: TrendsOptions): Promise<string>;
  export function relatedTopics(options: RelatedQueriesOptions): Promise<string>;
  export function relatedQueries(options: RelatedQueriesOptions): Promise<string>;
  export function autoComplete(options: AutocompleteOptions): Promise<string>;
  export function dailyTrends(options: { geo?: string; }): Promise<string>;
  export function realTimeTrends(options: { geo?: string; category?: string; }): Promise<string>;

  const googleTrends: {
    interestOverTime: typeof interestOverTime;
    interestByRegion: typeof interestByRegion;
    relatedTopics: typeof relatedTopics;
    relatedQueries: typeof relatedQueries;
    autoComplete: typeof autoComplete;
    dailyTrends: typeof dailyTrends;
    realTimeTrends: typeof realTimeTrends;
  };

  export default googleTrends;
}
