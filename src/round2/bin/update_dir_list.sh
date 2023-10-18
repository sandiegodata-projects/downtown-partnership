PROFILE=$1
BUCKET=ds.civicknowledge.org
ROOT_URL=http://$BUCKET
BASE_S3=s3://$BUCKET

 if [ -z "$PROFILE" ]; 
 then 
     echo "Usage: update_dir_list <aws_profile_name>"; 
     exit 1
 fi

IMAGES_PREFIX=downtownsandiego.org/homeless-count-201806
BASE_IMAGES=$BASE_S3/$IMAGES_PREFIX

# Update images
aws s3 ls $BASE_IMAGES --recursive | awk -v ROOT_URL=$ROOT_URL '{print ROOT_URL"/"$4}' | grep '.png' > /tmp/urls.txt
aws --profile $PROFILE s3 cp /tmp/urls.txt $BASE_IMAGES/urls.txt
aws --profile $PROFILE s3api put-object-acl --bucket $BUCKET --key $IMAGES_PREFIX/urls.txt --acl public-read
rm -f /tmp/urls.txt