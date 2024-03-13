for filename in *.sql; do
    if [ "$filename" != "install.sql" ]
    then
        echo $filename
        psql -h localhost -p 5432 -d postgres -U postgres --command 'SET client_min_messages TO WARNING;' --command "\i $filename;"
    fi
done