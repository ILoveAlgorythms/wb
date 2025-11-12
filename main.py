import download

async def main():
    await download.create_tables()
    print("Hello from wb!")


if __name__ == "__main__":
    main()
