from google.cloud import firestore


def delete_collection(coll_ref, batch_size):
    docs = list(coll_ref.limit(batch_size).stream())
    deleted = 0
    for doc in docs:
        # Recursively delete subcollections, if any
        for subcoll in doc.reference.collections():
            delete_collection(subcoll, batch_size)
        doc.reference.delete()
        deleted += 1
    if deleted >= batch_size:
        return delete_collection(coll_ref, batch_size)


def main():
    db = firestore.Client()
    lists_ref = db.collection("lists")
    delete_collection(lists_ref, 10)
    print("Firestore collection 'lists' deleted.")


if __name__ == "__main__":
    main()
