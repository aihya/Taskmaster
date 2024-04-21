#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

int main(int argc, char **argv, char** envp)
{
	int i = 0;
	int j = atoi(argv[1]);
	for (char **p = envp; p; p++)
		write(1, *p, strlen(*p));
	while (i < j)
	{
		sleep(1);
		i++;
	}
	return (0);
}
