
def run(ctx):

    resource = 'development-test-245814'
    username = 'user:joshua.delete@gmail.com'


    iam_client = ctx.get_client().get('iam', 'v1')

    request = iam_client.roles().list()
    while True:
        response = request.execute()

        for role in response.get('roles', []):
            # remove binding for user at organization level
            # remove binding for user at folder level
            # remove binding for user at project level
            # remove binding for user at resource level


            print(role)

        request = iam_client.roles().list_next(previous_request=request, previous_response=response)
        if request is None:
            break
