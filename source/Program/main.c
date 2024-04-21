#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main(int argc, char **argv, char** envp)
{
	int i = 0;
	int j = atoi(argv[1]);
	printf("Hello world\n");
	while (1)
	{
		sleep(1);
		i++;
	}
	return (0);
}
