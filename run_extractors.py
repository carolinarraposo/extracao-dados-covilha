from extractors.bluesky_extractor import run as run_bluesky
from extractors.facebook_extractor import run as run_facebook
from extractors.instagram_extractor import run as run_instagram
from extractors.threads_extractor import run as run_threads
from extractors.news_extractor import run as run_news
from extractors.reddit_extractor import run as run_reddit
from extractors.youtube_extractor import run as run_youtube


def main():
    print("===================================")
    print("INÍCIO DA EXTRAÇÃO AUTOMÁTICA")
    print("===================================")

    extractors = [
        ("Bluesky", run_bluesky),
        #("Facebook", run_facebook),
        #("Instagram", run_instagram),
        #("Threads", run_threads),
        ("News", run_news),
        ("Reddit", run_reddit),
        ("YouTube", run_youtube),
    ]

    for name, func in extractors:
        print(f"\n--- {name} ---")
        try:
            func()
            print(f"{name}: concluído.")
        except Exception as e:
            print(f"{name}: erro -> {e}")

    print("\n===================================")
    print("EXTRAÇÃO TERMINADA")
    print("===================================")


if __name__ == "__main__":
    main()
