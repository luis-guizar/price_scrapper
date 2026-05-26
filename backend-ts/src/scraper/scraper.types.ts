export interface ScrapeProgress {
    onProgress?: (scraped: number) => Promise<void>;
    onLog?: (message: string) => Promise<void>;
}
