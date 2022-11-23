import asyncio
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor
from itertools import islice
from typing import List

from pytube import Search, YouTube


class Searcher:
    def __init__(
        self,
        executor: ThreadPoolExecutor,
        additional_queries: List[str],
        primary_results=4,
        secondary_results=4,
    ):
        self.thread_executor = executor
        self.additional_queries = additional_queries
        self.primary_results = primary_results
        self.secondary_results = secondary_results

    def search(self, query: str) -> List[YouTube]:
        results = []

        SearchOperation = namedtuple("SearchOperation", "count query")

        searches = [SearchOperation(self.primary_results, query)]
        for additional in self.additional_queries:
            searches.append(
                SearchOperation(
                    self.secondary_results, "{} {}".format(query, additional)
                )
            )

        for search in searches:
            result = Search(search.query).results
            result = self.filter_results(result, search.count)
            results += result

        # remove duplicates
        return [i for n, i in enumerate(results) if i not in results[:n]]

    def filter_results(self, results: List[YouTube], count: int) -> List[YouTube]:
        def allow(yt: YouTube):
            if yt.length > 60 * 15:
                return False

            return True

        filtered = (r for r in results if allow(r))
        return list(islice(filtered, count))

    # we could parallelize all searches but it doesn't take that long
    # so we don't risk getting rate limited
    async def search_async(self, query: str) -> List[YouTube]:
        return await asyncio.get_event_loop().run_in_executor(
            self.thread_executor, self.search, query
        )
