# grubhub
parsing restaurants data products from grubhub

solution:
i have tried python request, python htmlsession modules to get htmls of the given urls but these pages aren't fetched using these modules.
before going to the selenium, tried to find their apis developer apis or other open ended apis, found some apis but these apis are authentication walls.
so i tried to find the way to get the bearer token to use these api. and eventually i found the way first to get their client id and using this client id
we can call their auth api returning the access and refresh token. after getting its simple to use their apis. their access token expired after one hour
so whenever i get status_code except 200 i tried to get new access token instead refreshing the token as i haven't found a way yet to refresh the token.
haven't opted for selenium because its much slower than this approach, took development time and yes selnium is much secure way to scrape the data.  
i haven't tested whether grubhub block ips or not, if they do so, we need to have some mechanism of IP rotation. one thing i have noticed 
it that their client id is same from last 3 days, dont know if its constant or changes over time, but i have written code to get client id at
the start of script. 

for scalablity point of view, i have used threading but if we have hundreds of thousands then we can use it as a lambda function on aws which will be triggered by SQS.
and restaurants links will be added in SQS, so everytime there is an entyr in SQS this function will be triggered and data will be scraped. 

for layout changes or schema changes, i haven't handled this thing yet, but as i am using their internal apis we can keep track of the change in response, like saving 
the old response and then comparing the new response, there is a python package diff_match_patch to highlight the changes between two string.
so we can do this in either case if we are using selenium or apis we can store html in case of selenium and api responses in case of apis to track the changes.



deployment:

There is a single python file written in python3 there are some packages you need to install csv, bs4, requests.  which you guys can run as python script 
to parse the data and get csv file in the same directory as a result.
scripts starts by taking grubhub restaurants valid links(restaurant ids at the end of url), like given in a code. also i have commented
recommendation products section which we can uncomment to also scrape recommended products. 
Have included multithreading for handling maximum requests at a time, for now thread limit is 2 and we can increase its limit.

