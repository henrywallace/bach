mkdir -p downloads

zips="bwv1007.zip bwv1008.zip bwv1009.zip bwv1010.zip bwv1011.zip bwv1012.zip"

for zip_file in $zips; do
    curl "http://www.jsbach.net/midi/$zip_file" > "downloads/$zip_file";
    (cd downloads/ && unzip -u $zip_file && rm $zip_file)
done

