from math import ceil

def paginate(query, page:int=1, page_size:int=20):
    total=query.count()
    pages=ceil(total/page_size)

    items=(
        query
        .offset((page-1)*page_size)
        .limit(page_size)
        .all()
    )

    return {
        "page":page,
        "page_size":page_size,
        "total":total,
        "pages":pages,
        "items":items
    }
