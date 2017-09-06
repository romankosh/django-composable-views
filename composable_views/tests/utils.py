def show_urls(urllist, depth=0):
    for entry in urllist:
        print(
            "  " * depth, entry.regex.pattern,
            '  ',
            getattr(entry, 'name', ''),
            getattr(entry, 'namespace', '')
        )
        if hasattr(entry, 'url_patterns'):
            show_urls(entry.url_patterns, depth + 1)
