
const CACHE_NAME = "language-bank-v1";

const FILES_TO_CACHE = [
	"/static/manifest.json",
"/static/icons/icon-192.png",
"/static/icons/icon-512.png"
];

self.addEventListener("install", (event) => {
	event.waitUntil(
		caches.open(CACHE_NAME).then((cache) => {
			return cache.addAll(FILES_TO_CACHE);
		})
	);
	
	self.skipWaiting();
});

self.addEventListener("activate", (event) => {
	event.waitUntil(
		caches.keys().then((keys) =>
		Promise.all(
			keys
			.filter((key) => key !== CACHE_NAME)
			.map((key) => caches.delete(key))
		)
		)
	);
	
	self.clients.claim();
});

self.addEventListener("fetch", (event) => {
	const request = event.request;
	const url = new URL(request.url);
	
	if (
		request.method === "GET" &&
		url.origin === self.location.origin &&
		url.pathname.startsWith("/static/")
	) {
		event.respondWith(
			caches.match(request).then((cached) => {
				return cached || fetch(request);
			})
		);
	}
});
