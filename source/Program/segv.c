#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>

int main(int argc, char **argv, char** envp)
{
	int i = 0;
	int j = atoi(argv[1]);
	char *p;
	sleep(j);
	while (i < 50000)
	{
		p = argv[i];
		i++;
	}
	return (0);
}
