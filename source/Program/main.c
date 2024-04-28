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
	while (i < 100)
	{
		// sleep(1);
		printf("%s", argv[i]);
		i++;
	}
	return (0);
}
