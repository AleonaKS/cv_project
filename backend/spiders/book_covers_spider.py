# backend/spiders/book_covers_spider.py

import scrapy
import pandas as pd
import os


class BookCoversSpider(scrapy.Spider):
    name = "book_covers"

    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS": 1,
        "LOG_LEVEL": "INFO",
        "USER_AGENT": "Mozilla/5.0"
    }

    def __init__(self, csv_path=None, limit=50, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.csv_path = csv_path or "backend/data/books_df.csv"
        self.limit = int(limit)

        self.output_csv = "backend/data/books_local.csv"
        self.images_dir = "backend/data/images"

        os.makedirs(self.images_dir, exist_ok=True)

        self.rows = []

    def start_requests(self):
        if not os.path.exists(self.csv_path):
            self.logger.error(f"CSV not found: {self.csv_path}")
            return

        df = (
            pd.read_csv(self.csv_path)
            .dropna(subset=["image_link"])
            .head(self.limit)
            .reset_index(drop=True)
        )

        self.logger.info(f"📚 Found {len(df)} books")

        for idx, row in df.iterrows():
            yield scrapy.Request(
                url=row["image_link"],
                callback=self.save_image,
                meta={
                    "id": idx,
                    "title": row.get("title", ""),
                    "genre": row.get("genre", ""),
                },
                errback=self.handle_error,
                dont_filter=True,
            )

    def save_image(self, response):
        book_id = response.meta["id"]
        title = response.meta["title"]
        genre = response.meta["genre"]

        filename = f"{book_id}.jpg"
        image_path = os.path.join(self.images_dir, filename)

        with open(image_path, "wb") as f:
            f.write(response.body)

        self.rows.append({
            "id": book_id,
            "title": title,
            "genre": genre,
            "image_path": image_path,
        })

        self.logger.info(f"✅ Saved {filename}")

    def handle_error(self, failure):
        self.logger.warning(f"❌ Failed: {failure.request.url}")

    def closed(self, reason):
        if not self.rows:
            self.logger.warning("No images downloaded")
            return

        df = pd.DataFrame(self.rows)
        df.to_csv(self.output_csv, index=False)

        self.logger.info(f"CSV saved: {self.output_csv}")
        self.logger.info(f"Images saved: {len(self.rows)}")
