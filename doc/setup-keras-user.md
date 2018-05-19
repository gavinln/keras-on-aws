## Setup the keras user on Amazon Web Services (AWS)

### Create the keras-vm user to run an AWS EC2 instance

1. Login to the AWS management console

    ```
    https://aws.amazon.com/console/
    ```

2. Go to the IAM console

    ```
    https://console.aws.amazon.com/iam/home
    ```

3. Select Users and click "Add User"

4. Enter the User name as keras-vm

5. Select Programmatic access

6. Click "Next: Permissions"

7. Select Attach existing policies directory and select AmazonEC2FullAccess

8. Click "Next: Review"

9. Click "Create User"

10. Click on "Download .csv"

11. Download the file "credentials.csv" to the keras-on-aws/do_not_checkin directory
